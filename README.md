# vim-ultest

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
   1. [Configuration](#configuration)
   2. [Commands](#commands)
   3. [Plug mappings](#plug-mappings)
5. [Debugging](#debugging)
6. [Feedback](#feedback)

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

NeoVim >= 0.4.4 is supported for now, but once 0.5 is released support will be dropped due to added complexity from handling missing features.

vim-ultest can be installed as usual with your favourite plugin manager.
**Note:** NeoVim users must run `:UpdateRemotePlugins` after install if they don't use a plugin manager that already does.

[**dein**](https://github.com/Shougo/dein.vim):

```vim
" Vim Only
call dein#add("roxma/nvim-yarp")
call dein#add("roxma/vim-hug-neovim-rpc")

call dein#add("janko/vim-test")
call dein#add("rcarriga/vim-ultest")
```

[**vim-plug**](https://github.com/junegunn/vim-plug)

```vim
" Vim Only
Plug "roxma/nvim-yarp"
Plug "roxma/vim-hug-neovim-rpc"

Plug "janko/vim-test"
Plug "rcarriga/vim-ultest", { "do": ":UpdateRemotePlugins" }
```

[packer.nvim](https://github.com/wbthomason/packer.nvim)

```lua
use { "rcarriga/vim-ultest", requires = {"janko/vim-test"}, run = ":UpdateRemotePlugins" }
```

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

**Note**: The window to show results relies on the 'updatetime' setting which by default is 4 seconds.
A longer 'updatetime' will mean the window takes longer to show automatically but a shorter time means (Neo)Vim will write to disk much more often which can degrade SSDs over time and cause slowdowns on HDDs.

### Commands

`:help ultest-commands`

For example to run the nearest test every time a file is written:

```vim
augroup UltestRunner
    au!
    au BufWritePost * UltestNearest
augroup END
```

**Need user contributions**

The `Ultest` command runs all tests in a file. For some test runners the plugin
can parse the output of the runner to get results so that they can all be run
as a single process. For other runners the tests all have to be run as
inidividual processes, which can have a significant performance impact. Please
check the wiki to see if your runner is supported.  If it is not please open an
issue with example output and I can add support for it!

### Plug mappings

`:help ultest-mappings`

For example to be able to jump between failures in a test file:

```vim
nmap ]t <Plug>(ultest-next-fail)
nmap [t <Plug>(ultest-prev-fail)
```

For configuration options and more documentation see `:h ultest`

## Debugging

`:help ultest-debugging`

Debugging with nvim-dap is supported but some user configuration is required.
See the [debugging recipes](https://github.com/rcarriga/vim-ultest/wiki/Debugging-Recipes) for some working configurations.
If you do not see one for your runner/language, please submit a change to the wiki so others can use it too!

## Feedback

Feel free to open an issue for bug reports, feature requests or suggestions.
I will try address them as soon as I can!
