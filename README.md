# Ultest

This plugin is in the early stages of development so there will likely be bugs!
If you experience any problems please open an issue with as much detail as possible i.e. error messages, file type, test runner and minimal example.
Only NeoVim is supported right as that is what I use myself.
There are no features absent from Vim that are required, so I plan to add Vim support at some stage.


1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
	1. [Configuration](#configuration)
	2. [Commands](#commands)
	3. [Plug mappings](#plug-mappings)
5. [Known Issues](#known-issues)
	1. [Virtual Text](#virtual-text)
6. [Feedback](#feedback)

## Introduction

_The ultimate testing plugin for NeoVim_

Running tests should be as quick and painless as possible.
[vim-test](https://github.com/janko/vim-test) is a very powerful and extensive testing plugin, but it can be cumbersome to configure and lacks some features to make it feel like an integrated piece of your editor.
Rather than replacing vim-test altogether, Ultest (in name and practice) builds upon vim-test to make it even better while maintaining the ability to use your existing configuration.
If you're already using vim-test then switching to Ultest is as easy as installing and... well, that's pretty much it.

The goal behind Ultest is to make running tests as seamless as possible.

- Tests are run individually so that any errors can be addressed individually.
- Tests are run in seperate threads (not just asynchronously on the same thread) so your Vim session will never be blocked.
- When tests are complete, results can be viewed immediately or on command.
- Utilise the existing power of vim-test by extending upon it.

## Features

- Easy to use interface for running tests
- Extensible and customisable
- Test result markers using signs or virtual text
- Failure outputs in a floating window

More features are being worked on.
If you have any ideas, feel free to open an issue!

## Installation

**Requirements**:

- Python >= 3.7
- NeoVim >= 0.5
- [Pynvim library](https://pynvim.readthedocs.io/en/latest/installation.html)
- [vim-test](https://github.com/janko/vim-test)

These are simply what I can guarantee work, I have not tested NeoVim < 0.5 or Python < 3.7.

Ultest can be installed as usual with your favourite plugin manager.

For example with [dein](https://github.com/Shougo/dein.vim):
```vim
call dein#add('janko/vim-test')
call dein#add('rcarriga/vim-ultest', {"depends": "vim-test"})
```

## Usage

### Configuration

Any vim-test configuration should carry over to Ultest.
See the vim-test documentation on further details for changing test runner and options.
If you have compatibility problems please raise an issue.

One change you will notice is that test output is not coloured.
This is due to the way the command is run.
To work around this you can simply tell your test runner to always output with colour.
For example
```vim
let test#python#pytest#options = "--color=yes"

let test#javascript#jest#options = "--color=always"
```

### Commands

- `Ultest`: Run all tests in a file.
- `UltestNearest`: Run the test closest to the cursor.
- `UltestOutput`: Show error output of the nearest test.

These can be used manually or in an autocommand.\
For example to run the nearest test every time a file is written:
```vim
augroup UltestRunner
    au!
    au BufWritePost * UltestNearest
augroup END
```

### Plug mappings

- `<Plug>(ultest-next-fail)`: Jump to next failed test.
- `<Plug>(ultest-prev-fail)`: Jump to previous failed test.
- `<Plug>(ultest-run-file)`: Run all tests in a file.
- `<Plug>(ultest-run-nearest)`: Run test closest to the cursor.
- `<Plug>(ultest-output-show) `: Show error output of the nearest test.
- `<Plug>(ultest-output-jump) `: Show error output of the nearest test.

Bind these to make running, navigating and analysing test results easier.\
For example to be able to jump between failures in a test file:
```vim
nmap <leader>uj <Plug>(ultest-next-fail)
nmap <leader>uk <Plug>(ultest-prev-fail)
```

Features are able to be enabled/disabled individually.
For toggling any feature check the help: `:h ultest`

## Feedback

Feel free to open an issue for bug reports, feature requests or suggestions.
I will try address them as soon as I can!
