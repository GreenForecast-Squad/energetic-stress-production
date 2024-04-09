import numpy as np
import pandas as pd
import numpy_indexed as npi
from keras import models, layers
import tensorflow as tf

HORIZONS_SLICES = {
    '00H24H': slice(0, 9), '27H48H': slice(9, 17), '51H72H': slice(17, 25), '75H102H': slice(25, 34)
}


def average_horizon(data):
    return np.stack([
        np.nanmean(data[:, sl, :], axis=1) for sl in HORIZONS_SLICES.values()
    ], axis=1)


def get_dataset():
    df_rte = pd.read_csv('clean_datasets/rte_agg_daily_2014_2024.csv')
    df_rte['Fossile'] = df_rte['Fioul'] + df_rte['Gaz']
    df_rte = df_rte.loc[df_rte['Consommation'] != 0, :]
    df_rte['Date'] = pd.to_datetime(df_rte['Date'])
    arpege_data = np.load('clean_datasets/arpege_data.npz', allow_pickle=True)
    return df_rte, {
        'dates': np.array([np.datetime64(d) for d in arpege_data['dates']]),
        'data': average_horizon(arpege_data['data'])
    }


def get_valid_dates(df_rte, arpege_data):
    arpege_dates = arpege_data['dates']
    valid_dates = [
        d for e_d, d in enumerate(arpege_dates)
        if (
                all(d + i * np.timedelta64(1, 'D') in df_rte['Date'].values for i in range(4)) and
                not np.any(np.isnan(arpege_data['data'][e_d, ...]))
        )
    ]
    return valid_dates


def convert_date_int(dates_arr):
    return (dates_arr - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')


def get_batch(batch_ds, df_rte, arpege_data):
    index_rte = npi.indices(convert_date_int(df_rte['Date'].values), convert_date_int(batch_ds))
    index_a = npi.indices(convert_date_int(arpege_data['dates']), convert_date_int(batch_ds))
    x = np.array([
        []
        for d in batch_ds
    ])
    y = np.array([
        0
        for d in batch_ds
    ])
    return x, y


def get_model():
    return models.Sequential([
        layers.Dense(64),
        layers.Dense(4)
    ])



if __name__ == '__main__':
    model = get_model()
    model_optimizer = tf.optimizers.Adam(learning_rate=0.001, beta_1=0.95, weight_decay=2. * 1e-5)
    df_rte, arpege_data = get_dataset()
    v_dates = get_valid_dates(df_rte, arpege_data)
    batch_size = 4
    nb_batches = len(v_dates) // batch_size - 1

    @tf.function
    def train_step(data):
        x, y = data
        with tf.GradientTape() as model_tape:
            y_pred = model(x)
            loss_model = tf.reduce_mean((y - y_pred) ** 2)
        gradients_of_model = model_tape.gradient(
            loss_model, model.trainable_variables
        )
        model_optimizer.apply_gradients(zip(gradients_of_model, model.trainable_variables))
        return loss_model

    for epoch in range(8):
        loss_state = 0.
        for b in range(nb_batches):
            batch_ds = np.array(v_dates[b*batch_size:(b+1)*batch_size])
            batch = get_batch(batch_ds)
            loss_state += train_step(batch)
            if b % 10 == 9:
                print(loss_state / b)

