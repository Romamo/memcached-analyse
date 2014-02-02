# -*- coding: utf-8 -*-

# Additional patterns to group keys
PATTERN_GROUP = (
)

# These keys will be replaced with % to group
PATTERN_KEY = (
                  r'\w{32}', # x86c0642135bc64806f5105547c052fc9 (MD5)
                  r'\d+', # x123 xxx123xxx
)

# Group name for ungroupped keys
NOGROUP = 'nogroup'

REPORTS_DEFAULT = (
    ('k', 'miss', 10),
    ('g', 'miss', 10),
    ('g', 'size', 5),
    ('g', 'hitp', 10),
    ('g', 'hitp', -10),
)