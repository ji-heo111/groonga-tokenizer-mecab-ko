# Copyright (C) 2026  Sutou Kouhei <kou@clear-code.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# * Ubuntu 22.04: 3.22
cmake_minimum_required(VERSION 3.22)

message(STATUS "CMake: ${CMAKE_VERSION}")

# https://cmake.org/cmake/help/latest/policy/CMP0077.html
#
# option() honors normal variables.
cmake_policy(SET CMP0077 NEW)

project(
    groonga-tokenizer-mecab-ko
    VERSION "1.0.0"
    DESCRIPTION "Groonga tokenizer for mecab-ko"
    LANGUAGES C
)

message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")

if(NOT DEFINED CMAKE_C_STANDARD)
    set(CMAKE_C_STANDARD 99)
endif()
set(CMAKE_C_STANDARD_REQUIRED TRUE)

include(GNUInstallDirs)

if(NOT DEFINED GROONGA_TOKENIZER_MECAB_KO_DOC_DIR)
    set(GROONGA_TOKENIZER_MECAB_KO_DOC_DIR
        "${CMAKE_INSTALL_DOCDIR}/${PROJECT_NAME}"
    )
endif()
if(NOT DEFINED GROONGA_TOKENIZER_MECAB_KO_LIB_DIR)
    set(GROONGA_TOKENIZER_MECAB_KO_LIB_DIR
        "${CMAKE_INSTALL_LIBDIR}/${PROJECT_NAME}"
    )
endif()
if(NOT DEFINED GROONGA_TOKENIZER_MECAB_KO_SYSCONF_DIR)
    set(GROONGA_TOKENIZER_MECAB_KO_SYSCONF_DIR
        "${CMAKE_INSTALL_SYSCONFDIR}/${PROJECT_NAME}"
    )
endif()

find_package(Groonga REQUIRED)

find_program(MECAB_KO_CONFIG "mecab-config")
if(MECAB_KO_CONFIG AND EXISTS ${MECAB_KO_CONFIG})
    execute_process(
        COMMAND ${MECAB_KO_CONFIG} --inc-dir
        COMMAND_ERROR_IS_FATAL ANY
        OUTPUT_VARIABLE MECAB_KO_INCLUDE_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    execute_process(
        COMMAND ${MECAB_KO_CONFIG} --libs-only-L
        COMMAND_ERROR_IS_FATAL ANY
        OUTPUT_VARIABLE MECAB_KO_LIBRARY_DIRS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    find_library(
        MECAB_KO_LIBRARY
        NAMES mecab
        PATHS ${MECAB_KO_LIBRARY_DIRS}
        REQUIRED
        NO_DEFAULT_PATH
    )
    add_library(libmecab_ko INTERFACE)
    target_include_directories(
        libmecab_ko
        SYSTEM
        INTERFACE ${MECAB_KO_INCLUDE_DIRS}
    )
    target_link_libraries(libmecab_ko INTERFACE ${MECAB_KO_LIBRARY})
else()
    include(ExternalProject)
    include(ProcessorCount)
    ProcessorCount(NPROC)
    if(NPROC EQUAL 0)
        set(NPROC 1)
    endif()

    set(MECAB_KO_LIBRARY_RELATIVE
        "lib/${CMAKE_STATIC_LIBRARY_PREFIX}mecab${CMAKE_STATIC_LIBRARY_SUFFIX}"
    )
    ExternalProject_Add(
        mecab_ko_external
        URL
            https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz
        CONFIGURE_COMMAND
            <SOURCE_DIR>/configure --prefix=<INSTALL_DIR> --enable-static
            --disable-shared --with-pic
        BUILD_COMMAND make -j${NPROC}
        INSTALL_COMMAND make install
        BUILD_IN_SOURCE FALSE
        BUILD_BYPRODUCTS <INSTALL_DIR>/${MECAB_KO_LIBRARY_RELATIVE}
    )
    ExternalProject_Get_Property(mecab_ko_external SOURCE_DIR)
    set(MECAB_KO_SOURCE_DIR ${SOURCE_DIR})
    ExternalProject_Get_Property(mecab_ko_external INSTALL_DIR)
    set(MECAB_KO_INSTALL_DIR ${INSTALL_DIR})
    install(
        FILES
            ${MECAB_KO_SOURCE_DIR}/AUTHORS
            ${MECAB_KO_SOURCE_DIR}/BSD
            ${MECAB_KO_SOURCE_DIR}/COPYING
            ${MECAB_KO_SOURCE_DIR}/GPL
            ${MECAB_KO_SOURCE_DIR}/LGPL
        DESTINATION "${GROONGA_TOKENIZER_MECAB_KO_DOC_DIR}/mecab-ko"
    )

    set(MECAB_KO_RC_PATH "${GROONGA_TOKENIZER_MECAB_KO_SYSCONF_DIR}/mecabrc")
    if(IS_ABSOLUTE ${MECAB_KO_RC_PATH})
        set(MECAB_KO_RC_PATH_ABSOLUTE ${MECAB_KO_RC_PATH})
    else()
        set(MECAB_KO_RC_PATH_ABSOLUTE)
        cmake_path(
            APPEND MECAB_KO_RC_PATH_ABSOLUTE
            ${CMAKE_INSTALL_PREFIX}
            ${MECAB_KO_RC_PATH}
        )
    endif()
    set(MECAB_KO_DIC_DIR
        "${GROONGA_TOKENIZER_MECAB_KO_LIB_DIR}/dic/mecab-ko-dic"
    )

    add_library(libmecab_ko INTERFACE)
    target_include_directories(
        libmecab_ko
        INTERFACE ${MECAB_KO_INSTALL_DIR}/include
    )
    find_package(Threads REQUIRED)
    target_link_libraries(
        libmecab_ko
        INTERFACE
            ${MECAB_KO_INSTALL_DIR}/${MECAB_KO_LIBRARY_RELATIVE}
            Threads::Threads
    )
    target_compile_definitions(
        libmecab_ko
        INTERFACE
            GRN_WITH_BUNDLED_MECAB_KO
            GRN_BUNDLED_MECAB_KO_RC_PATH="${MECAB_KO_RC_PATH_ABSOLUTE}"
    )

    ExternalProject_Add(
        mecab_ko_dic_external
        URL
            https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz
        DEPENDS mecab_ko_external
        PATCH_COMMAND ./autogen.sh
        CONFIGURE_COMMAND
            ./configure --prefix=<INSTALL_DIR>
            --with-mecab-config=${MECAB_KO_INSTALL_DIR}/bin/mecab-config
        BUILD_COMMAND make -j${NPROC}
        BUILD_IN_SOURCE TRUE
        INSTALL_COMMAND make install
    )
    ExternalProject_Get_Property(mecab_ko_dic_external SOURCE_DIR)
    set(MECAB_KO_DIC_SOURCE_DIR ${SOURCE_DIR})
    install(
        FILES
            ${MECAB_KO_DIC_SOURCE_DIR}/AUTHORS
            ${MECAB_KO_DIC_SOURCE_DIR}/COPYING
        DESTINATION "${GROONGA_TOKENIZER_MECAB_KO_DOC_DIR}/mecab-ko-dic"
    )

    add_dependencies(libmecab_ko mecab_ko_dic_external)

    if(IS_ABSOLUTE ${MECAB_KO_DIC_DIR})
        set(MECAB_KO_DIC_DIR_ABSOLUTE ${MECAB_KO_DIC_DIR})
    else()
        set(MECAB_KO_DIC_DIR_ABSOLUTE)
        cmake_path(
            APPEND MECAB_KO_DIC_DIR_ABSOLUTE
            ${CMAKE_INSTALL_PREFIX}
            ${MECAB_KO_DIC_DIR}
        )
    endif()
    configure_file(mecabrc.in mecabrc @ONLY)
    install(
        FILES ${CMAKE_CURRENT_BINARY_DIR}/mecabrc
        DESTINATION "${GROONGA_TOKENIZER_MECAB_KO_SYSCONF_DIR}"
    )
    install(
        DIRECTORY ${MECAB_KO_INSTALL_DIR}/lib/mecab/dic/mecab-ko-dic
        DESTINATION "${MECAB_KO_DIC_DIR}/.."
    )
endif()

add_subdirectory(tokenizers)

install(
    FILES "COPYING" "README.md"
    DESTINATION "${GROONGA_TOKENIZER_MECAB_KO_DOC_DIR}"
)
