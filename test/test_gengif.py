import os
import sys
import unittest

# Ensure src directory is in sys.path
_test_dir = str(os.path.dirname(os.path.abspath(__file__)))
_src_dir = str(os.path.abspath(os.path.join(_test_dir, '..', 'src')))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from gengif import generate_gif


class TestGengif(unittest.TestCase):
    """Test suite for gengif.py."""

    def test_generate_gif(self):
        test_dir = str(os.path.dirname(os.path.abspath(__file__)))
        project_root = str(os.path.dirname(test_dir))
        jpg_dir = str(os.path.join(project_root, 'testdata', 'img'))
        ref_img_dir = str(os.path.join(project_root, 'testdata', 'refimg'))
        output_dir = str(os.path.join(project_root, 'testdata', 'result'))
        output_path = str(os.path.join(output_dir, 'output.gif'))

        if os.path.exists(output_path):
            os.remove(output_path)

        result_path = generate_gif(
            jpg_dir=jpg_dir,
            ref_img_dir=ref_img_dir,
            output_path=output_path,
            duration=400
        )

        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(output_path), f"Expected GIF file at {output_path} does not exist.")
        self.assertGreater(os.path.getsize(output_path), 0, "Generated GIF file is empty.")


if __name__ == '__main__':
    unittest.main()
