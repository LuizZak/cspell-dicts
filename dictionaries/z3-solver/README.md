# CSpell Z3 Solver Dictionary

Z3 Solver dictionary for cspell.

This is a pre-built dictionary for use with CSpell.

## Installation

Global Install and add to CSpell global settings.

```sh
npm install -g @cspell/dict-z3-solver
cspell link add @cspell/dict-z3-solver
```

## Uninstall from CSpell

```sh
cspell link remove @cspell/dict-z3-solver
```

## Manual Installation

Manual installation is useful if you want to include this dictionary as part of your CI/CD lint process.

```
npm i @cspell/dict-z3-solver
```

The `cspell-ext.json` file in this package should be added to the import section in your `cspell.json` file.

```javascript
{
    // …
    "import": ["@cspell/dict-z3-solver/cspell-ext.json"],
    // …
}
```

# Dictionary Development

See: [How to Create a New Dictionary](https://github.com/streetsidesoftware/cspell-dicts#how-to-create-a-new-dictionary)

## License

MIT

> Some packages may have other licenses included.
