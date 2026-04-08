%global mecab_ko_version 0.9.2
%global mecab_ko_engine_version 0.996
%global mecab_ko_dic_version 2.1.1
%global mecab_ko_dic_date 20180720

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

Requires:       mecab-ko = %{version}-%{release}
Requires:       mecab-ko-dic = %{version}-%{release}
Requires:       groonga-libs

%description
A Groonga tokenizer plugin that uses mecab-ko for Korean
morphological analysis. It enables Korean full-text search
in Groonga.

# ---- mecab-ko sub-package ----
%package -n mecab-ko
Summary:        Korean morphological analyzer based on MeCab (engine %{mecab_ko_engine_version})
License:        GPLv2 or LGPLv2 or BSD
Provides:       mecab-ko-engine = %{mecab_ko_engine_version}
Provides:       mecab = %{mecab_ko_engine_version}
Conflicts:      mecab

%description -n mecab-ko
mecab-ko is a Korean morphological analyzer forked from MeCab.
Engine version: %{mecab_ko_engine_version}

%post -n mecab-ko -p /sbin/ldconfig
%postun -n mecab-ko -p /sbin/ldconfig

# ---- mecab-ko-dic sub-package ----
%package -n mecab-ko-dic
Summary:        Korean dictionary for mecab-ko (dictionary %{mecab_ko_dic_version})
Requires:       mecab-ko = %{version}-%{release}
Provides:       mecab-ko-dictionary = %{mecab_ko_dic_version}

%description -n mecab-ko-dic
Korean dictionary data for mecab-ko morphological analyzer.
Dictionary version: %{mecab_ko_dic_version}

%post -n mecab-ko-dic
# Set dicdir in mecabrc to mecab-ko-dic
for f in /usr/etc/mecabrc /etc/mecabrc; do
  if [ -f "$f" ]; then
    sed -i 's|^dicdir.*|dicdir = %{_libdir}/mecab/dic/mecab-ko-dic|' "$f"
  fi
done
# /usr/lib -> /usr/lib64 symlink (lib64 systems)
if [ ! -d /usr/lib/mecab ] && [ -d %{_libdir}/mecab ]; then
  ln -s %{_libdir}/mecab /usr/lib/mecab
fi

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
# Step 1: Build mecab-ko -> staging
MECAB_STAGING=%{_builddir}/mecab-ko-staging
mkdir -p ${MECAB_STAGING}

pushd mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}
mkdir -p _build && cd _build
../configure --prefix=/usr --libdir=%{_libdir}
make %{?_smp_mflags}
# Install to system directly since mecab-ko-dic build requires mecab-dict-index
make install
make install DESTDIR=${MECAB_STAGING}
ldconfig
popd

# Step 2: Build mecab-ko-dic
pushd mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}
./autogen.sh
./configure --prefix=/usr --libdir=%{_libdir} \
  --with-dicdir=%{_libdir}/mecab/dic/mecab-ko-dic
make %{?_smp_mflags}
popd

# Step 3: Build groonga-tokenizer-mecab-ko
cmake -S . -B _build -GNinja -DCMAKE_INSTALL_PREFIX=/usr
cmake --build _build

# ===========================================================
# install
# ===========================================================
%install
# Install mecab-ko
pushd mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/_build
make install DESTDIR=%{buildroot}
popd

# Install mecab-ko-dic
pushd mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}
make install DESTDIR=%{buildroot}
popd

# Install groonga-tokenizer-mecab-ko
DESTDIR=%{buildroot} cmake --install _build

# ===========================================================
# files
# ===========================================================
%files
%license COPYING
%doc README.md
%{_libdir}/groonga/plugins/tokenizers/mecab_ko.so
%exclude %{_docdir}/%{name}

%files -n mecab-ko
%{_bindir}/mecab
%{_bindir}/mecab-config
%{_includedir}/mecab.h
%{_libdir}/libmecab.so
%{_libdir}/libmecab.so.*
%{_libexecdir}/mecab/
%{_mandir}/man1/mecab.1*
%config(noreplace) /usr/etc/mecabrc
%exclude %{_libdir}/libmecab.la
%exclude %{_libdir}/libmecab.a

%files -n mecab-ko-dic
%{_libdir}/mecab/dic/mecab-ko-dic/

%changelog
* Tue Apr 07 2026 groonga-tokenizer-mecab-ko developers - 1.0.0-1
- Initial RPM release
