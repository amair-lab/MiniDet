import sounddevice as sd
import numpy as np


def simple_mic_test():
    # First, let's just list the devices
    print("Available devices:")
    print(sd.query_devices())

    # Get the default input device
    device_info = sd.query_devices(kind='input')
    print("\nDefault input device:")
    print(device_info)

    input("Press Enter to start a 3-second recording test...")

    # Record some audio
    duration = 3  # seconds
    sample_rate = int(device_info['default_samplerate'])

    try:
        recording = sd.rec(
            frames=duration * sample_rate,
            samplerate=sample_rate,
            channels=1,
            blocking=True
        )
        print("\nRecording complete!")

        input("Press Enter to play back...")
        sd.play(recording, sample_rate)
        sd.wait()
        print("Playback complete!")

    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying alternative approach with explicit device selection...")

        # List all devices with input channels
        input_devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev['max_input_channels'] > 0:
                input_devices.append((i, dev['name']))
                print(f"{i}: {dev['name']}")

        if input_devices:
            device_num = int(input("Select device number to try: "))
            try:
                recording = sd.rec(
                    frames=duration * sample_rate,
                    samplerate=sample_rate,
                    channels=1,
                    device=device_num,
                    blocking=True
                )
                print("\nRecording complete!")

                input("Press Enter to play back...")
                sd.play(recording, sample_rate)
                sd.wait()
                print("Playback complete!")
            except Exception as e2:
                print(f"Still getting error: {e2}")
                print("\nDebug info:")
                print(f"Selected device: {sd.query_devices(device=device_num)}")


if __name__ == "__main__":
    simple_mic_test()