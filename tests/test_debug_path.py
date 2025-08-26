"""Debug test to check Python path and import."""
import sys
import os

def test_debug_paths():
    """Debug Python path and imports."""
    print(f"\n=== DEBUG INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"__file__ path: {__file__}")
    print(f"tests directory: {os.path.dirname(__file__)}")
    print(f"project root: {os.path.dirname(os.path.dirname(__file__))}")
    
    print(f"\nPython path:")
    for i, p in enumerate(sys.path[:8]):
        print(f"  [{i}] {p}")
    
    project_root = os.path.dirname(os.path.dirname(__file__))
    custom_components_path = os.path.join(project_root, "custom_components")
    whenhub_path = os.path.join(custom_components_path, "whenhub")
    
    print(f"\n=== FILE CHECKS ===")
    print(f"custom_components exists: {os.path.exists(custom_components_path)}")
    print(f"whenhub exists: {os.path.exists(whenhub_path)}")
    print(f"whenhub/__init__.py exists: {os.path.exists(os.path.join(whenhub_path, '__init__.py'))}")
    
    # List files in custom_components
    if os.path.exists(custom_components_path):
        print(f"Files in custom_components: {os.listdir(custom_components_path)}")
    
    # List files in whenhub
    if os.path.exists(whenhub_path):
        files = os.listdir(whenhub_path)[:10]  # Limit to first 10
        print(f"Files in whenhub: {files}")
    
    # Try import
    print(f"\n=== IMPORT TEST ===")
    try:
        import custom_components
        print(f"✅ custom_components imported")
        print(f"custom_components.__file__: {custom_components.__file__}")
    except Exception as e:
        print(f"❌ custom_components import failed: {e}")
    
    try:
        import custom_components.whenhub
        print(f"✅ custom_components.whenhub imported")
    except Exception as e:
        print(f"❌ custom_components.whenhub import failed: {e}")
    
    assert True  # Always pass, we just want to see the debug output