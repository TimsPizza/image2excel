import base64


class ImageUtils:

    @staticmethod
    async def from_file(image_path):
        """
        Read an image file and return its base64 representation.
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return encoded_string
        except Exception as e:
            raise ValueError(f"Failed to encode image: {str(e)}")
