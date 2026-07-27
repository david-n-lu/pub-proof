from PySide6.QtCore import QObject, Signal

from product_building.product_import import create_product_index_cache


class ProductIndexWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress = Signal(str, int)

    def __init__(
        self,
        products_dir,
        cache_path,
        sku_column,
        product_name_column,
        description_column,
    ):
        super().__init__()

        self.products_dir = products_dir
        self.cache_path = cache_path
        self.sku_column = sku_column
        self.product_name_column = product_name_column
        self.description_column = description_column

    def run(self):
        try:
            create_product_index_cache(
                self.products_dir,
                self.cache_path,
                sku_column=self.sku_column,
                product_name_column=self.product_name_column,
                description_column=self.description_column,
                progress_callback=self.progress.emit,
            )

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))