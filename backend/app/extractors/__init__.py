"""
Extractor Registry System

Extractors are automatically discovered and registered.
To add a new extractor:
1. Create a file in this directory
2. Inherit from BaseExtractor
3. Use @register_extractor decorator

Example:
    @register_extractor("simplegameguide")
    class SimpleGameGuideExtractor(BaseExtractor):
        def can_handle(self, url: str) -> bool:
            return "simplegameguide.com" in url
        
        def extract(self, html: str, date: str) -> List[ExtractedLink]:
            # Your extraction logic
            pass
"""

from typing import Dict, Type, List
from .base import BaseExtractor

# Global registry of extractors
_EXTRACTOR_REGISTRY: Dict[str, Type[BaseExtractor]] = {}


def register_extractor(name: str):
    """Decorator to register an extractor class."""
    def decorator(cls: Type[BaseExtractor]):
        _EXTRACTOR_REGISTRY[name] = cls
        cls._extractor_name = name
        return cls
    return decorator


def get_extractor(name: str) -> BaseExtractor:
    """Get an extractor instance by name."""
    if name not in _EXTRACTOR_REGISTRY:
        raise ValueError(f"Unknown extractor: {name}. Available: {list(_EXTRACTOR_REGISTRY.keys())}")
    return _EXTRACTOR_REGISTRY[name]()


def get_extractor_for_url(url: str) -> BaseExtractor:
    """Auto-detect which extractor to use based on URL."""
    for name, extractor_class in _EXTRACTOR_REGISTRY.items():
        extractor = extractor_class()
        if extractor.can_handle(url):
            return extractor
    
    # Fallback to default extractor
    if "default" in _EXTRACTOR_REGISTRY:
        return _EXTRACTOR_REGISTRY["default"]()
    
    raise ValueError(f"No extractor found for URL: {url}")


def list_extractors() -> List[str]:
    """List all registered extractors."""
    return list(_EXTRACTOR_REGISTRY.keys())


# Import all extractors to trigger registration
# This must happen after register_extractor is defined
from . import simplegameguide, default, mosttechs, crazyashwin

# Register them manually
_EXTRACTOR_REGISTRY[simplegameguide.SimpleGameGuideExtractor._extractor_name] = simplegameguide.SimpleGameGuideExtractor
_EXTRACTOR_REGISTRY[default.DefaultExtractor._extractor_name] = default.DefaultExtractor
_EXTRACTOR_REGISTRY[mosttechs.MostTechsExtractor._extractor_name] = mosttechs.MostTechsExtractor
_EXTRACTOR_REGISTRY[crazyashwin.CrazyAshwinExtractor._extractor_name] = crazyashwin.CrazyAshwinExtractor

