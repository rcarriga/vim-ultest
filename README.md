# Ultest

This plugin is in the early stages of development so there will likely be bugs!
If you experience any problems please open an issue with as much detail as possible i.e. error messages, file type, test runner and minimal example.


1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
	1. [Configuration](#configuration)
	2. [Commands](#commands)
	3. [Plug mappings](#plug-mappings)
6. [Feedback](#feedback)

## Introduction

_The ultimate testing plugin for NeoVim_

![output_example](https://user-images.githubusercontent.com/24252670/107156823-7f707300-6978-11eb-9900-5bef5b1a036b.gif)
![summary_example](https://user-images.githubusercontent.com/24252670/107156859-a5961300-6978-11eb-8a73-4b61433da4a4.gif)

Running tests should be as quick and painless as possible.
[vim-test](https://github.com/janko/vim-test) is a very powerful and extensive testing plugin, but it can be cumbersome to configure and lacks some features to make it feel like an integrated piece of your editor.
Rather than replacing vim-test altogether, Ultest (in name and practice) builds upon vim-test to make it even better while maintaining the ability to use your existing configuration.
If you're already using vim-test then switching to Ultest is as easy as installing and... well, that's pretty much it.

The goal behind Ultest is to make running tests as seamless as possible.

- Tests are run individually so that any errors can be addressed individually.
- Tests are run in separate threads (not just asynchronously on the same thread) so your NeoVim session will never be blocked.
- When tests are complete, results can be viewed immediately or on command.
- Utilise the existing power of vim-test by extending upon it.

## Features

- Summary window
  - Highlight tests based on current status (running, succeeded, failed)
  - Show test output
  - View all tests currently found in all test files
- Test result markers using signs or virtual text
- Failure outputs in a floating window
- Extensible and customisable

More features are being worked on.
If you have any ideas, feel free to open an issue!

## Installation

**Requirements**:

All users:

- Python >= 3.7
- [Pynvim library](https://pynvim.readthedocs.io/en/latest/installation.html)
- [vim-test](https://github.com/janko/vim-test)

Vim only:
- [nvim-yarp](https://github.com/roxma/nvim-yarp)
- [vim-hug-neovim-rpc](https://github.com/roxma/vim-hug-neovim-rpc)

**Note:** Vim support is not in a usable state.
The instructions here should only be used if you wish to contribute fixes.
There is no fundamental issue blocking Vim support, I just don't have the time.
Feel free to open PRs for adding support but I will not be addressing bug reports for Vim.

I have not had the chance to extensively test NeoVim versions, it is recommended to stay on the latest nightly version.
If you have issues with missing features, please open an issue with your editor version.

Ultest can be installed as usual with your favourite plugin manager.

For example with [dein](https://github.com/Shougo/dein.vim):
```vim
" Vim Only
call dein#add("roxma/nvim-yarp")
call dein#add("roxma/vim-hug-neovim-rpc")

call dein#add('janko/vim-test')
call dein#add('rcarriga/vim-ultest')
```

**Note:** NeoVim users must run `:UpdateRemotePlugins` after install if they don't use a plugin manager that already does.

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
- `UltestSummary`: Toggle the summary window

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
- `<Plug>(ultest-summary-toggle) `: Toggle summary window.
- `<Plug>(ultest-summary-jump) `: Jump to summary window

Bind these to make running, navigating and analysing test results easier.\
For example to be able to jump between failures in a test file:
```vim
nmap ]t <Plug>(ultest-next-fail)
nmap [t <Plug>(ultest-prev-fail)
```

Features are able to be enabled/disabled individually.
For toggling any feature check the help: `:h ultest`

## Feedback

Feel free to open an issue for bug reports, feature requests or suggestions.
I will try address them as soon as I can!
