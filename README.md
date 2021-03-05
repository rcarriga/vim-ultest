# vim-ultest

This plugin is in the early stages of development so there will likely be bugs!
If you experience any problems please open an issue with as much detail as possible i.e. error messages, file type, test runner and minimal example.

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
   1. [Configuration](#configuration)
   2. [Commands](#commands)
   3. [Plug mappings](#plug-mappings)
5. [Feedback](#feedback)

## Introduction

_The ultimate testing plugin for NeoVim_

Running tests should be as quick and painless as possible.
[vim-test](https://github.com/janko/vim-test) is a very powerful and extensive testing plugin, but it can be cumbersome to configure and lacks some features to make it feel like an integrated piece of your editor.

Rather than replacing vim-test altogether, vim-ultest (in name and practice) builds upon vim-test to make it even better while maintaining the ability to use your existing configuration.
If you're already using vim-test then switching to vim-ultest is as easy as installing and... well, that's pretty much it.

The goal behind vim-ultest is to make running tests as seamless as possible.

## Features

- Run tests and view results individually
  - Test result markers using signs or virtual text
  - Failure outputs in a floating window
  - Key mappings to jump between failed tests
  - Stop long running tests

![Running Example](https://user-images.githubusercontent.com/24252670/107279654-39d2a980-6a4f-11eb-95f5-074f69b856e6.gif)

- Attach to running processes to debug
  - Currently experimental so please report issues!
  - Uses python's readline library to pass input

![debugging](https://user-images.githubusercontent.com/24252670/107827860-8552c380-6d7f-11eb-8f69-04f95e048cfb.gif)

- Summary window
  - Highlight tests based on current status (running, succeeded, failed)
  - Show test output
  - View all tests currently found in all test files
  - Run tests with key binding

![summary](https://user-images.githubusercontent.com/24252670/110024777-6b752280-7d26-11eb-9594-76005bbcfa48.gif)

- Multithreaded (not just asynchronous) to prevent blocking

- Use existing vim-test configuration

- Customisable

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

**Note:** Vim support is maintained with a best effort.
Due to the differences between Vim and NeoVim and their RPC libraries, it is inevitable that bugs will occur in one and not the other.
I primarily use NeoVim so I will catch issues in it myself.
Please file bug reports for Vim if you find them!

I have not had the chance to extensively test (Neo)Vim versions, it is recommended to stay on the latest nightly version.
If you have issues with missing features, please open an issue with your editor version.

vim-ultest can be installed as usual with your favourite plugin manager.

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

`:help ultest-config`

Any vim-test configuration should carry over to vim-ultest.
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

`:help ultest-commands`

For example to run the nearest test every time a file is written:

```vim
augroup UltestRunner
    au!
    au BufWritePost * UltestNearest
augroup END
```

### Plug mappings

`:help ultest-mappings`

For example to be able to jump between failures in a test file:

```vim
nmap ]t <Plug>(ultest-next-fail)
nmap [t <Plug>(ultest-prev-fail)
```

For configuration options and more documentation see `:h ultest`

## Feedback

Feel free to open an issue for bug reports, feature requests or suggestions.
I will try address them as soon as I can!
