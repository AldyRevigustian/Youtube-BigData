import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)


def run_tests():
    print("🧪 Running YouTube Sentiment Analysis System Tests")
    print("=" * 60)

    try:
        print("\n1️⃣ Running System Component Tests...")
        from tests.test_system import main as test_system_main

        test_system_main()
    except Exception as e:
        print(f"❌ System tests failed: {e}")

    try:
        print("\n2️⃣ Running Data Flow Tests...")
        from tests.test_data_flow import main as test_dataflow_main

        test_dataflow_main()
    except Exception as e:
        print(f"❌ Data flow tests failed: {e}")

    print("\n✅ Test suite completed!")


if __name__ == "__main__":
    run_tests()
