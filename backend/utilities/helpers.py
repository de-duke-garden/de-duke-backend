def property_image_upload_handler(self, filename):
        """
        Custom handler for the upload_to parameter of the ImageField.
        """
        return f'property/{self.property.id}/images/{filename}'