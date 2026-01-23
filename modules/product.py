class ProductData:
    """
    This class contains information regarding a product within a specific time period it is meant to hold information
    temporarly for the data gathering script in the insert bulk report function. It does not contain information about
    which warehouse the data refers to.
    """
    def __init__(self, product_name, product_code, unit_type, inicial_stock, final_stock, contifico_id = None):
        self.product_name = product_name
        self.product_code = product_code
        self.unit_type = unit_type
        self.contifico_id = contifico_id
        self.inicial_stock = inicial_stock
        self.final_stock = final_stock

    def __str__(self):
        return ", ".join(map(str, [self.product_name, self.product_code,
                                   self.unit_type, self.contifico_id,
                                   self.inicial_stock, self.final_stock]))