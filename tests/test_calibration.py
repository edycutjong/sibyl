from unittest.mock import MagicMock

import pytest

from sibyl import calibration as calibration_module
from sibyl.calibration import (
    calibrate_predictions,
    calibrate_probability,
    load_calibration_model,
    train_calibration_model,
)


@pytest.fixture(autouse=True)
def reset_calibration_model():
    calibration_module._calibration_model = None
    yield
    calibration_module._calibration_model = None


def test_load_calibration_model_missing(mocker):
    mocker.patch("os.path.exists", return_value=False)
    assert not load_calibration_model("fake/path.pkl")


def test_load_calibration_model_success(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mock_pickle_load = mocker.patch("sibyl.calibration.pickle.load", return_value="fake_model")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    assert load_calibration_model("fake/path.pkl")
    mock_open.assert_called_once_with("fake/path.pkl", "rb")
    mock_pickle_load.assert_called_once()
    assert calibration_module._calibration_model == "fake_model"


def test_load_calibration_model_exception(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", side_effect=Exception("Read error"))

    assert not load_calibration_model("fake/path.pkl")


def test_calibrate_probability_no_model():
    assert calibrate_probability(0.7) == 0.7


def test_calibrate_probability_with_model():
    mock_model = MagicMock()
    # predict_proba returns a 2D array: [[prob_class_0, prob_class_1]]
    mock_model.predict_proba.return_value = [[0.2, 0.85]]
    calibration_module._calibration_model = mock_model

    val = calibrate_probability(0.7)
    assert val == 0.85


def test_calibrate_probability_clamping():
    mock_model = MagicMock()
    # test upper clamp
    mock_model.predict_proba.return_value = [[0.0, 1.5]]
    calibration_module._calibration_model = mock_model
    assert calibrate_probability(0.7) == 0.99

    # test lower clamp
    mock_model.predict_proba.return_value = [[1.0, -0.5]]
    assert calibrate_probability(0.7) == 0.01


def test_calibrate_probability_exception(caplog):
    mock_model = MagicMock()
    mock_model.predict_proba.side_effect = Exception("Model error")
    calibration_module._calibration_model = mock_model

    val = calibrate_probability(0.7)
    assert val == 0.7
    assert "Calibration failed" in caplog.text


def test_calibrate_predictions_no_model():
    preds = {"Yes": 0.6, "No": 0.4}
    assert calibrate_predictions(preds) == preds


def test_calibrate_predictions_with_model(mocker):
    mock_model = MagicMock()
    # Mock calibrate_probability instead of predict_proba to control exact outputs
    mocker.patch("sibyl.calibration.calibrate_probability", side_effect=[0.4, 0.4])
    calibration_module._calibration_model = mock_model

    preds = {"Yes": 0.6, "No": 0.4}
    calibrated = calibrate_predictions(preds)

    # They sum to 0.8, should be renormalized to 0.5 each
    assert calibrated == {"Yes": 0.5, "No": 0.5}


def test_train_calibration_model(mocker):
    mock_lr_class = mocker.patch("sklearn.linear_model.LogisticRegression")
    mock_lr_instance = mock_lr_class.return_value

    mocker.patch("os.makedirs")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_pickle_dump = mocker.patch("sibyl.calibration.pickle.dump")

    raw_probs = [0.1, 0.9]
    actual = [0, 1]

    model = train_calibration_model(raw_probs, actual, "fake/save.pkl")

    assert model == mock_lr_instance
    mock_lr_instance.fit.assert_called_once()
    mock_open.assert_called_once_with("fake/save.pkl", "wb")
    mock_pickle_dump.assert_called_once_with(mock_lr_instance, mock_open.return_value)
    assert calibration_module._calibration_model == mock_lr_instance
