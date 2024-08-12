# Copyright 2017-2020 Palantir Technologies, Inc.
# Copyright 2021- Python Language Server Contributors.

import logging

from pylsp import _utils, hookimpl

log = logging.getLogger(__name__)


@hookimpl
def pylsp_hover(config, document, position):
    settings = config.plugin_settings("jedi_hover", document_path=document.path)
    code_position = _utils.position_to_jedi_linecolumn(document, position)
    definitions = document.jedi_script(use_document_path=True).infer(**code_position)
    word = document.word_at_position(position)

    # Find first exact matching definition
    definition = next((x for x in definitions if x.name == word), None)

    # Ensure a definition is used if only one is available
    # even if the word doesn't match. An example of this case is 'np'
    # where 'numpy' doesn't match with 'np'. Same for NumPy ufuncs
    if len(definitions) == 1:
        definition = definitions[0]

    if not definition:
        return {"contents": ""}

    hover_capabilities = config.capabilities.get("textDocument", {}).get("hover", {})
    supported_markup_kinds = hover_capabilities.get("contentFormat", ["markdown"])
    preferred_markup_kind = _utils.choose_markup_kind(supported_markup_kinds)

    # Find first exact matching signature
    signature = next(
        (
            x.to_string()
            for x in definition.get_signatures()
            if (x.name == word and x.type not in ["module"])
        ),
        "",
    )

    include_docstring = settings.get("include_docstring", True)

    # raw docstring returns only doc, without signature
    docstring = definition.docstring(raw=True)
    if include_docstring is False:
        if signature:
            docstring = ""
        else:
            docstring = docstring.strip().split("\n")[0].strip()

    return {
        "contents": _utils.format_docstring(
            docstring,
            preferred_markup_kind,
            signatures=[signature] if signature else None,
        )
    }
