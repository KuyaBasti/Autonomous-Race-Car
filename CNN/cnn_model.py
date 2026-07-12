import os
import pandas as pd
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split

# Configuration
USE_BITMASKS_ONLY = True  # Set to False to use both images and bitmasks

# Parameters
BASE_DIR = 'data/run_1/output/selected_data'
IMAGE_DIR = os.path.join(BASE_DIR, 'images')
BITMASK_DIR = os.path.join(BASE_DIR, 'bitmasks')
CSV_PATH = os.path.join(BASE_DIR, 'selected_data.csv')
IMG_HEIGHT, IMG_WIDTH = 66, 200  # Can be adjusted
BATCH_SIZE = 32
EPOCHS = 10

# Load CSV
df = pd.read_csv(CSV_PATH)

# Filter out missing files
df['bitmask_path'] = df['image'].apply(lambda x: os.path.join(BITMASK_DIR, x.replace('.png', '_mask.png')))
if not USE_BITMASKS_ONLY:
    df['image_path'] = df['image'].apply(lambda x: os.path.join(IMAGE_DIR, x))
    df = df[df['image_path'].apply(os.path.exists) & df['bitmask_path'].apply(os.path.exists)]
else:
    df = df[df['bitmask_path'].apply(os.path.exists)]

print(f"Found {len(df)} valid {'bitmask' if USE_BITMASKS_ONLY else 'image-bitmask'} pairs")

# Load data
def load_data(row):
    if USE_BITMASKS_ONLY:
        # Load and preprocess bitmask only
        mask = cv2.imread(row['bitmask_path'], cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (IMG_WIDTH, IMG_HEIGHT))
        mask = mask.astype(np.float32) / 255.0  # Normalize
        return np.expand_dims(mask, axis=-1)  # Add channel dimension
    else:
        # Load and preprocess both image and bitmask
        img = cv2.imread(row['image_path'])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB
        img = cv2.resize(img, (IMG_WIDTH, IMG_HEIGHT))
        img = img.astype(np.float32) / 255.0  # Normalize
        
        mask = cv2.imread(row['bitmask_path'], cv2.IMREAD_GRAYSCALE)
        mask = cv2.resize(mask, (IMG_WIDTH, IMG_HEIGHT))
        mask = mask.astype(np.float32) / 255.0  # Normalize
        
        # Combine image and bitmask
        return np.concatenate([img, np.expand_dims(mask, axis=-1)], axis=-1)

# Load all data
print("Loading data...")
X = np.array([load_data(row) for _, row in df.iterrows()])
y = df[['steering_angle', 'speed']].values.astype(np.float32)

print(f"Input shape: {X.shape}")
print(f"Output shape: {y.shape}")

# Train/Val split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Build the CNN model
input_channels = 1 if USE_BITMASKS_ONLY else 4
model = models.Sequential([
    # Input shape: (height, width, channels) - either 1 for bitmask or 4 for RGB+bitmask
    layers.Input(shape=(IMG_HEIGHT, IMG_WIDTH, input_channels)),
    
    # Convolutional layers
    layers.Conv2D(24, (5,5), strides=(2,2), activation='relu'),
    layers.Conv2D(36, (5,5), strides=(2,2), activation='relu'),
    layers.Conv2D(48, (5,5), strides=(2,2), activation='relu'),
    layers.Conv2D(64, (3,3), activation='relu'),
    layers.Conv2D(64, (3,3), activation='relu'),
    
    # Flatten and dense layers
    layers.Flatten(),
    layers.Dense(100, activation='relu'),
    layers.Dropout(0.5),  # Add dropout for regularization
    layers.Dense(50, activation='relu'),
    layers.Dropout(0.3),  # Add dropout for regularization
    layers.Dense(10, activation='relu'),
    layers.Dense(2)  # Output: steering_angle and speed
])

# Compile model
model.compile(
    optimizer='adam',
    loss='mse',
    metrics=['mae']
)

model.summary()

# Create model checkpoint callback
model_type = 'bitmask_only' if USE_BITMASKS_ONLY else 'image_bitmask'
checkpoint_path = os.path.join(BASE_DIR, f'model_checkpoints_{model_type}')
os.makedirs(checkpoint_path, exist_ok=True)
checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=os.path.join(checkpoint_path, 'model_epoch_{epoch:02d}.h5'),
    save_best_only=True,
    monitor='val_loss',
    mode='min'
)

# Train
print(f"\nStarting training with {'bitmasks only' if USE_BITMASKS_ONLY else 'images and bitmasks'}...")
history = model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=[checkpoint_callback]
)

# Save final model
model.save(os.path.join(BASE_DIR, f'final_model_{model_type}.h5'))
print(f"\nModel saved to {os.path.join(BASE_DIR, f'final_model_{model_type}.h5')}")
