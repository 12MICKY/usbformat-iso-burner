import unittest

from iso_gui import device_flags_text, extract_dd_progress_bytes, format_device, mounted_partitions


class IsoGuiHelpersTest(unittest.TestCase):
    def test_device_flags_text(self) -> None:
        device = {"rm": True, "hotplug": True, "tran": "usb"}
        self.assertEqual(device_flags_text(device), "removable, hotplug, usb")

    def test_device_flags_text_fixed_device(self) -> None:
        self.assertEqual(device_flags_text({"rm": False, "hotplug": False, "tran": "sata"}), "fixed")

    def test_mounted_partitions(self) -> None:
        device = {
            "children": [
                {"path": "/dev/sdb1", "mountpoints": ["/media/usb"]},
                {"path": "/dev/sdb2", "mountpoints": [None]},
            ]
        }
        self.assertEqual(mounted_partitions(device), ["/dev/sdb1"])

    def test_format_device(self) -> None:
        device = {
            "path": "/dev/sdb",
            "size": "14.9G",
            "model": "Flash Disk",
            "rm": True,
            "hotplug": True,
            "tran": "usb",
        }
        text = format_device(device)
        self.assertIn("Flash Disk", text)
        self.assertIn("/dev/sdb", text)
        self.assertIn("14.9G", text)

    def test_extract_dd_progress_bytes(self) -> None:
        line = "104857600 bytes (105 MB, 100 MiB) copied, 2 s, 52.4 MB/s"
        self.assertEqual(extract_dd_progress_bytes(line), 104857600)

    def test_extract_dd_progress_bytes_invalid_line(self) -> None:
        self.assertIsNone(extract_dd_progress_bytes("Writing ISO. This may take several minutes ..."))


if __name__ == "__main__":
    unittest.main()
