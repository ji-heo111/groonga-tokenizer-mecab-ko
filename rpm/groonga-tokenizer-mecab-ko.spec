%global mecab_ko_version 0.9.2
%global mecab_ko_engine_version 0.996
%global mecab_ko_dic_version 2.1.1
%global mecab_ko_dic_date 20180720

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

Requires:       mecab-ko = %{mecab_ko_engine_version}
Requires:       mecab-ko-dic = %{mecab_ko_dic_version}
Requires:       groonga-libs

%description
A Groonga tokenizer plugin that uses mecab-ko for Korean
morphological analysis. It enables Korean full-text search
in Groonga.

# ---- mecab-ko sub-package ----
%package -n mecab-ko
Version:        %{mecab_ko_engine_version}
Summary:        Korean morphological analyzer based on MeCab
License:        GPLv2 or LGPLv2 or BSD

%description -n mecab-ko
mecab-ko is a Korean morphological analyzer forked from MeCab.

%post -n mecab-ko -p /sbin/ldconfig
%postun -n mecab-ko -p /sbin/ldconfig

# ---- mecab-ko-dic sub-package ----
%package -n mecab-ko-dic
Version:        %{mecab_ko_dic_version}
Summary:        Korean dictionary for mecab-ko
Requires:       mecab-ko = %{mecab_ko_engine_version}

%description -n mecab-ko-dic
Korean dictionary data for mecab-ko morphological analyzer.

%post -n mecab-ko-dic
# mecabrc의 dicdir을 mecab-ko-dic으로 설정
for f in /usr/etc/mecabrc /etc/mecabrc; do
  if [ -f "$f" ]; then
    sed -i 's|^dicdir.*|dicdir = %{_libdir}/mecab/dic/mecab-ko-dic|' "$f"
  fi
done
# /usr/lib -> /usr/lib64 symlink (lib64 시스템)
if [ ! -d /usr/lib/mecab ] && [ -d %{_libdir}/mecab ]; then
  ln -s %{_libdir}/mecab /usr/lib/mecab
fi

# ===========================================================
# prep
# ===========================================================
%prep
%setup -q -n %{name}-%{version}
%setup -q -T -D -a 1
%setup -q -T -D -a 2

# config.guess/config.sub 업데이트 (ARM64 호환)
cp -f /usr/share/automake-*/config.guess mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/
cp -f /usr/share/automake-*/config.sub   mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/

# ===========================================================
# build
# ===========================================================
%build
# 1단계: mecab-ko 빌드 → 스테이징
MECAB_STAGING=%{_builddir}/mecab-ko-staging
mkdir -p ${MECAB_STAGING}

pushd mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}
mkdir -p _build && cd _build
../configure --prefix=/usr --libdir=%{_libdir}
make %{?_smp_mflags}
make install DESTDIR=${MECAB_STAGING}
popd

# 스테이징의 mecab-config를 PATH에 추가
export PATH="${MECAB_STAGING}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${MECAB_STAGING}%{_libdir}:${LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="${MECAB_STAGING}%{_libdir}/pkgconfig:${PKG_CONFIG_PATH}"

# 2단계: mecab-ko-dic 빌드 → 스테이징
pushd mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}
./autogen.sh
./configure --prefix=/usr --libdir=%{_libdir} \
  --with-dicdir=%{_libdir}/mecab/dic/mecab-ko-dic
make %{?_smp_mflags}
popd

# 3단계: groonga-tokenizer-mecab-ko 빌드
cmake -S . -B _build -GNinja -DCMAKE_INSTALL_PREFIX=/usr
cmake --build _build

# ===========================================================
# install
# ===========================================================
%install
# mecab-ko 설치
pushd mecab-%{mecab_ko_engine_version}-ko-%{mecab_ko_version}/_build
make install DESTDIR=%{buildroot}
popd

# mecab-ko-dic 설치
pushd mecab-ko-dic-%{mecab_ko_dic_version}-%{mecab_ko_dic_date}
make install DESTDIR=%{buildroot}
popd

# groonga-tokenizer-mecab-ko 설치
DESTDIR=%{buildroot} cmake --install _build

# ===========================================================
# files
# ===========================================================
%files
%license COPYING
%doc README.md
%{_libdir}/groonga/plugins/tokenizers/mecab_ko.so

%files -n mecab-ko
%{_bindir}/mecab
%{_bindir}/mecab-config
%{_includedir}/mecab.h
%{_libdir}/libmecab.so
%{_libdir}/libmecab.so.*
%config(noreplace) /usr/etc/mecabrc
%exclude %{_libdir}/libmecab.la

%files -n mecab-ko-dic
%{_libdir}/mecab/dic/mecab-ko-dic/

%changelog
* Mon Apr 07 2026 groonga-tokenizer-mecab-ko developers - 1.0.0-1
- Initial RPM release
