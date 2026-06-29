import base64
import unittest

from meme_studio.studio_security import decode_uploads, safe_upload_name


def encoded(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


class StudioUploadDecodeTest(unittest.TestCase):
    def test_decode_uploads_accepts_data_urls_and_bare_base64(self):
        uploads = [
            {"name": "avatar.png", "data": f"data:image/png;base64,{encoded(b'png-bytes')}"},
            {"name": "frame.webp", "data": encoded(b"webp-bytes")},
        ]

        decoded = decode_uploads(uploads, max_files=2, max_file_bytes=16)

        self.assertEqual(
            decoded,
            [
                {"name": "avatar.png", "data": b"png-bytes"},
                {"name": "frame.webp", "data": b"webp-bytes"},
            ],
        )

    def test_decode_uploads_rejects_invalid_base64(self):
        with self.assertRaisesRegex(ValueError, "base64"):
            decode_uploads([{"name": "bad.png", "data": "not base64!"}])

    def test_decode_uploads_normalizes_path_name_to_basename(self):
        decoded = decode_uploads([{"name": "../evil.png", "data": encoded(b"safe")}])

        self.assertEqual(decoded, [{"name": "evil.png", "data": b"safe"}])
        self.assertEqual(safe_upload_name(r"nested\evil.jpeg"), "evil.jpeg")

    def test_decode_uploads_rejects_too_large_file(self):
        with self.assertRaisesRegex(ValueError, "too large"):
            decode_uploads([{"name": "large.png", "data": encoded(b"12345")}], max_file_bytes=4)

    def test_decode_uploads_rejects_too_many_files(self):
        uploads = [
            {"name": "one.png", "data": encoded(b"1")},
            {"name": "two.png", "data": encoded(b"2")},
        ]

        with self.assertRaisesRegex(ValueError, "too many"):
            decode_uploads(uploads, max_files=1)

    def test_decode_uploads_rejects_disallowed_extensions(self):
        with self.assertRaisesRegex(ValueError, "extension"):
            decode_uploads([{"name": "script.svg", "data": encoded(b"<svg></svg>")}])

    def test_decode_uploads_rejects_mismatched_data_url_media_type(self):
        with self.assertRaisesRegex(ValueError, "media type"):
            decode_uploads([{"name": "avatar.gif", "data": f"data:image/png;base64,{encoded(b'png')}"}])


if __name__ == "__main__":
    unittest.main()
