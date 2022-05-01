import argparse
from models.crnn import *
from utils.generals import *
from utils.datasets import *
from utils.losses import *
from utils.callbacks import *
import tensorflow as tf
from tensorflow import keras
import os
import matplotlib.pyplot as plt

def run(
        pretrained,
        epochs,
        batch_size,
        train_data,
        val_data,
        lr,
        reduce_lr_patience,
        early_stop_patience,
        target_height,
        target_width,
        label_length,
        grayscale,
        invert_color,
        dilate,
        normalize,
        binarize,
        threshold,
        shuffle,
        cache,
):
    image_shape = (target_height, target_width) + (3 if not grayscale else 1,)

    if pretrained is not None:
        model = keras.models.load_model(pretrained)
        print(f'Load pretrained model: {pretrained}')
    else:
        model = get_model(image_shape=image_shape, vocab_size=CHAR_TO_NUM.vocabulary_size())
        print("Load new model")
    print(model.summary())

    train_dataset = get_tf_dataset(
        img_dir=train_data,
        label_path=os.path.join(train_data, 'labels.json'),
        target_size=(target_height, target_width),
        label_length=label_length,
        batch_size=batch_size,
        grayscale=grayscale,
        invert_color=invert_color,
        dilate=dilate,
        normalize=normalize,
        binarize=binarize,
        threshold=threshold,
        shuffle=shuffle,
        cache=cache
    )
    val_dataset = get_tf_dataset(
        img_dir=val_data,
        label_path=os.path.join(val_data, 'labels.json'),
        target_size=(target_height, target_width),
        label_length=label_length,
        batch_size=batch_size,
        grayscale=grayscale,
        invert_color=invert_color,
        dilate=dilate,
        normalize=normalize,
        binarize=binarize,
        threshold=threshold,
        shuffle=False,
        cache=cache
    )

    model.compile(
        optimizer=keras.optimizers.SGD(
            learning_rate=lr,
            momentum=0.9,
            nesterov=True
        ),
        loss=CTCLoss
    )

    callbacks = [
        keras.callbacks.ReduceLROnPlateau(monitor='loss', factor=0.1, patience=reduce_lr_patience, verbose=1),
        keras.callbacks.EarlyStopping(monitor='val_loss', patience=early_stop_patience, verbose=1,
                                      restore_best_weights=True),
        keras.callbacks.ModelCheckpoint(filepath='saved_models/htr', save_best_only=True),
        CallbackEval(val_dataset)
    ]

    history = model.fit(
        train_dataset,
        epochs=epochs,
        shuffle=True,
        validation_data=val_dataset,
        callbacks=callbacks
    )

    epoch_range = range(1, len(history.history['loss']) + 1)
    plt.plot(epoch_range, history.history['loss'], label='loss')
    plt.plot(epoch_range, history.history['val_loss'], label='val_loss')
    plt.xlabel('epoch')
    plt.ylabel('loss')
    plt.legend()
    plt.savefig('loss.jpg')
    plt.show()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()

    ap.add_argument('--pretrained', default=None, type=str)
    ap.add_argument('--epochs', default=54, type=int)
    ap.add_argument('--batch-size', default=32, type=int)
    ap.add_argument('--train-data', default='data/data_samples_2', type=str)
    ap.add_argument('--val-data', default='data/private_test', type=str)
    ap.add_argument('--lr', default=1e-4, type=float)
    ap.add_argument('--reduce-lr-patience', default=4, type=int)
    ap.add_argument('--early-stop-patience', default=10, type=int)
    ap.add_argument('--target-height', default=124, type=int)  # 69 133
    ap.add_argument('--target-width', default=1900, type=int)  # 773 1925
    ap.add_argument('--label-length', default=125, type=int)
    ap.add_argument('--grayscale', default=True, type=bool)
    ap.add_argument('--invert-color', default=False, type=bool)
    ap.add_argument('--dilate', default=0, type=int)
    ap.add_argument('--normalize', default=True, type=bool)
    ap.add_argument('--binarize', default=False, type=bool)
    ap.add_argument('--threshold', default=0.5, type=float)
    ap.add_argument('--shuffle', default=False, type=bool)
    ap.add_argument('--cache', default=False, type=bool)

    args = vars(ap.parse_args())

    run(**args)


