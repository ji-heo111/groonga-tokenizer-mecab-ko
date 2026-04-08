%global mecab_ko_version 0.9.2
%global mecab_ko_engine_version 0.996
%global mecab_ko_dic_version 2.1.1
%global mecab_ko_dic_date 20180720
%global mecab_ko_prefix %{_libdir}/groonga/tokenizer-mecab-ko

%global debug_package %{nil}

Name:           groonga-tokenizer-mecab-ko
Version:        1.0.0
Release:        1%{?dist}
Summary:        Groonga tokenizer plugin for Korean using mecab-ko
License:        LGPLv2+
URL:            https://github.com/groonga/groonga-tokenizer-mecab-ko

Source0:        %{name}-%{version}.tar.gz
Source1:        mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}.tar.gz
Source2:        mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}.tar.gz

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  cmake >= 3.22
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  groonga-devel
BuildRequires:  make
BuildRequires:  ninja-build

Requires:       groonga-libs

%description
A Groonga tokenizer plugin that uses mecab-ko for Korean
morphological analysis. It bundles mecab-ko and mecab-ko-dic
in a private prefix to avoid conflicts with system mecab.

# ===========================================================
# prep
# ===========================================================
%prep
%setup -q
%setup -q -T -D -a 1
%setup -q -T -D -a 2

# Update config.guess/config.sub (ARM64 compatibility)
cp -f /usr/share/automake-*/config.guess mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/
cp -f /usr/share/automake-*/config.sub   mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/

# ===========================================================
# build
# ===========================================================
%build
MECAB_KO_PREFIX=%{mecab_ko_prefix}

# Step 1: Build mecab-ko with private prefix
pushd mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}
mkdir -p _build && cd _build
../configure \
  --prefix=${MECAB_KO_PREFIX} \
  --libdir=${MECAB_KO_PREFIX}/lib \
  --disable-static
make %{?_smp_mflags}
# Install to build host so mecab-dict-index is available for dictionary build
make install
ldconfig ${MECAB_KO_PREFIX}/lib
popd

# Step 2: Build mecab-ko-dic with private prefix
export LD_LIBRARY_PATH=${MECAB_KO_PREFIX}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PATH=${MECAB_KO_PREFIX}/bin:${PATH}

pushd mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}
./autogen.sh
./configure \
  --prefix=${MECAB_KO_PREFIX} \
  --with-mecab-config=${MECAB_KO_PREFIX}/bin/mecab-config \
  --with-dicdir=${MECAB_KO_PREFIX}/lib/mecab/dic/mecab-ko-dic
make %{?_smp_mflags}
popd

# Step 3: Build groonga-tokenizer-mecab-ko with RPATH
cmake -S . -B _build -GNinja \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DMECAB_KO_PRIVATE_PREFIX=${MECAB_KO_PREFIX}
cmake --build _build

# ===========================================================
# install
# ===========================================================
%install
MECAB_KO_PREFIX=%{mecab_ko_prefix}

# Install mecab-ko
pushd mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/_build
make install DESTDIR=%{buildroot}
popd

# Install mecab-ko-dic
pushd mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}
make install DESTDIR=%{buildroot}
popd

# Set dicdir in mecabrc to private dictionary path
sed -i "s|^dicdir.*|dicdir = ${MECAB_KO_PREFIX}/lib/mecab/dic/mecab-ko-dic|" \
  %{buildroot}${MECAB_KO_PREFIX}/etc/mecabrc

# Install groonga-tokenizer-mecab-ko plugin
DESTDIR=%{buildroot} cmake --install _build

# Remove unnecessary files
rm -f %{buildroot}${MECAB_KO_PREFIX}/lib/libmecab.la
rm -f %{buildroot}${MECAB_KO_PREFIX}/lib/libmecab.a
rm -rf %{buildroot}${MECAB_KO_PREFIX}/bin
rm -rf %{buildroot}${MECAB_KO_PREFIX}/include
rm -rf %{buildroot}${MECAB_KO_PREFIX}/libexec
rm -rf %{buildroot}${MECAB_KO_PREFIX}/share

# ===========================================================
# files
# ===========================================================
%files
%license COPYING
%doc README.md
%{_libdir}/groonga/plugins/tokenizers/mecab_ko.so
%dir %{mecab_ko_prefix}
%{mecab_ko_prefix}/etc/
%{mecab_ko_prefix}/lib/
%exclude %{_docdir}/%{name}

%changelog
* Wed Apr 08 2026 groonga-tokenizer-mecab-ko developers - 1.0.0-1
- Bundle mecab-ko and mecab-ko-dic in private prefix
- Remove system mecab conflicts
