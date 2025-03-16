load("@rules_android//android:rules.bzl", "android_binary", "android_library")

android_library(
    name = "app_with_dependencies_lib",
    srcs = glob(["src/main/java/**/*.java"]),
    custom_package = "com.example.sample",
    manifest = "src/main/AndroidManifest.xml",
    resource_files = glob(["src/main/res/**"]),
    visibility = ["//visibility:private"],
    deps = [
        "@android_deps//:androidx_annotation_annotation",
        "@android_deps//:androidx_appcompat_appcompat",
        "@android_deps//:androidx_emoji2_emoji2",
        "@android_deps//:androidx_lifecycle_lifecycle_common",
        "@android_deps//:androidx_lifecycle_lifecycle_runtime",
    ],
)

android_binary(
    name = "app_with_dependencies",
    custom_package = "com.example.sample",
    manifest = "src/main/AndroidManifest.xml",
    resource_files = glob(["src/main/res/**"]),
    deps = [":app_with_dependencies_lib"],
)
