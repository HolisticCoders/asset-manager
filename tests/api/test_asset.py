from asset_manager.api.asset import AssetModel
from asset_manager.api.config import FOLDER_IDS


class TestAssetModel:
    def test_qt_model(self, google_drive, qtmodeltester):
        model = AssetModel(google_drive, FOLDER_IDS)
        qtmodeltester.check(model)

