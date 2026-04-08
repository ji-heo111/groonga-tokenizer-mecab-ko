# mecab-ko tokenizer for Groonga

A [Groonga](https://groonga.org/) tokenizer plugin that uses
[mecab-ko](https://bitbucket.org/eunjeon/mecab-ko) for Korean
morphological analysis. It enables Korean full-text search in
Groonga.

mecab-ko and mecab-ko-dic are bundled in a private prefix to
avoid conflicts with system mecab.

## Install

### From packages (recommended)

Download the latest package from
[Releases](https://github.com/groonga/groonga-tokenizer-mecab-ko/releases).

#### RPM (AlmaLinux 8/9, Amazon Linux 2023)

```bash
# Install Groonga first
# See: https://groonga.org/docs/install.html

sudo rpm -i groonga-tokenizer-mecab-ko-*.rpm
```

#### deb (Ubuntu, Debian bookworm)

```bash
# Install Groonga first
# See: https://groonga.org/docs/install.html

sudo dpkg -i groonga-tokenizer-mecab-ko_*.deb
```

### From source

#### Dependencies

- [Groonga](https://groonga.org/) and development headers
- CMake 3.22 or later
- Ninja (recommended) or Make
- A C99 compiler
- autoconf, automake (for building bundled mecab-ko)

#### Build

```bash
# Build mecab-ko to a private prefix
MECAB_KO_PREFIX=/usr/lib/groonga/tokenizer-mecab-ko

tar xf vendor/mecab-0.996-ko-0.9.2.tar.gz
mkdir -p mecab-ko.build && cd mecab-ko.build
../mecab-0.996-ko-0.9.2/configure \
  --prefix=${MECAB_KO_PREFIX} \
  --libdir=${MECAB_KO_PREFIX}/lib \
  --disable-static
make -j$(nproc)
sudo make install
sudo ldconfig ${MECAB_KO_PREFIX}/lib
cd ..

# Build mecab-ko-dic
export LD_LIBRARY_PATH=${MECAB_KO_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=${MECAB_KO_PREFIX}/bin:${PATH}

tar xf vendor/mecab-ko-dic-2.1.1-20180720.tar.gz
cd mecab-ko-dic-2.1.1-20180720
./autogen.sh
./configure \
  --prefix=${MECAB_KO_PREFIX} \
  --with-mecab-config=${MECAB_KO_PREFIX}/bin/mecab-config \
  --with-dicdir=${MECAB_KO_PREFIX}/lib/mecab/dic/mecab-ko-dic
make -j$(nproc)
sudo make install
sudo sed -i "s|^dicdir.*|dicdir = ${MECAB_KO_PREFIX}/lib/mecab/dic/mecab-ko-dic|" \
  ${MECAB_KO_PREFIX}/etc/mecabrc
cd ..

# Build and install the tokenizer plugin
cmake -S . -B build -GNinja \
  -DMECAB_KO_PRIVATE_PREFIX=${MECAB_KO_PREFIX}
cmake --build build
sudo cmake --install build
```

## Usage

Register the plugin and use `TokenMeCabKo` as the tokenizer:

```
plugin_register tokenizers/mecab_ko

tokenize TokenMeCabKo '안녕하세요'
```

You can use it in a table definition:

```
table_create Entries TABLE_NO_KEY
column_create Entries content COLUMN_SCALAR ShortText

table_create Terms TABLE_PAT_KEY ShortText \
  --default_tokenizer TokenMeCabKo \
  --normalizer NormalizerNFKC130
column_create Terms entries_content \
  COLUMN_INDEX|WITH_POSITION Entries content
```

### Options

`TokenMeCabKo` supports the following options:

- `chunked_tokenize`: Enable chunked processing for large text.
- `chunk_size_threshold`: Chunk size limit in bytes (default:
  8192).
- `include_class`: Include part-of-speech class in output.
- `include_reading`: Include reading in output.
- `include_form`: Include word form in output.
- `use_reading`: Use reading instead of surface form.
- `use_base_form`: Use dictionary base form.
- `target_classes`: Filter tokens by part-of-speech class.

### Environment variables

- `GRN_MECAB_KO_CHUNKED_TOKENIZE_ENABLED`: Enable chunked
  tokenization (`yes` or `no`).
- `GRN_MECAB_KO_CHUNK_SIZE_THRESHOLD`: Chunk size threshold in
  bytes (default: `8192`).

## Supported platforms

| Platform | Package |
|----------|---------|
| AlmaLinux 8 | RPM |
| AlmaLinux 9 | RPM |
| Amazon Linux 2023 | RPM |
| Ubuntu (latest) | deb |
| Debian bookworm | deb |

## License

LGPLv2.1 or later. See [COPYING](COPYING) for details.
