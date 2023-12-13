# Intellisense and Emacs
*Guides here are intended to help those navigate the "advanced developer" path. **None** of these guides are required to successfully install, customize or run Mother Tongues dictionares. If these guides are Greek to you, feel free to skip them.*

VS Code
--------------
If you are using [Visual Studio Code](https://code.visualstudio.com/), you can add the [schema to your for intellisense](https://code.visualstudio.com/docs/languages/json#:~:text=The%20association%20of%20a%20JSON,under%20the%20property%20json.schemas%20.)!

```json
"json.schemas": [
        {
            "fileMatch": [
                "config.mtd.json"
            ],
            "url": "https://raw.githubusercontent.com/MotherTongues/mothertongues/main/mothertongues/schemas/config.json"
        }
    ]s
```

Emacs
-------
For Emacs with [lsp-mode](https://emacs-lsp.github.io/lsp-mode/) you can add this to your `.emacs`
file (or use `M-x customize-variable lsp-json-schemas`):

```lisp
(setq lsp-json-schemas
    `[(:fileMatch ["config.mtd.json"]
        :url "https://raw.githubusercontent.com/MotherTongues/mothertongues/main/mothertongues/schemas/config.json")])
```
