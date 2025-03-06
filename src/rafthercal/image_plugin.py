import requests
from PIL import Image
from io import BytesIO

from rafthercal.plugin import BasePlugin

class ImagePlugin(BasePlugin):
    def get_context(self):
        c = self.get_config()
        response = requests.get(c.IMAGE_URL)
        img = Image.open(BytesIO(response.content))
        l = getattr(c, "IMAGE_CROP_LEFT", 0)
        t = getattr(c, "IMAGE_CROP_TOP", 0)
        r = getattr(c, "IMAGE_CROP_RIGHT", img.size[0])
        b = getattr(c, "IMAGE_CROP_BOTTOM", img.size[1])
        cropped_img = img.crop((l, t, r, b))
        cropped_img.save(c.IMAGE_OUTPUT_PATH)

        return {
            'image': "{ image " + c.IMAGE_OUTPUT_PATH + "}",
        }
