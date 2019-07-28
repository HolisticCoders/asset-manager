from asset_manager.api.asset import AssetModel

ROOT_ID = "TO_BE_FILLED"


class TestAssetModel:
    def test_qt_model(self, google_drive, qtmodeltester):
        model = AssetModel(google_drive, [ROOT_ID])
        qtmodeltester.check(model)

