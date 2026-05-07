#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared constants for SVG/JSON update workflows."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IdMapping:
    """Pair a CSS class with the ID prefix used for rewritten identifiers."""

    css_class: str
    prefix: str

KV = IdMapping(css_class="kv", prefix="awg-kv-")
LINKBOX = IdMapping(css_class="link-box", prefix="awg-lb-")
TKK = IdMapping(css_class="tkk", prefix="awg-tkk-")
