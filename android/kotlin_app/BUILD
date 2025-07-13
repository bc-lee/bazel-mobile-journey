load("@rules_android//android:rules.bzl", "android_binary")
load("@rules_kotlin//kotlin:android.bzl", "kt_android_library")

kt_android_library(
    name = "kotlin_app_lib",
    srcs = glob(["src/main/kotlin/**/*.kt"]),
    manifest = "src/main/AndroidManifest.xml",
    resource_files = glob(["src/main/res/**"]),
    visibility = ["//visibility:private"],
)

android_binary(
    name = "kotlin_app",
    custom_package = "com.example.kotlinapp",
    manifest = "src/main/AndroidManifest.xml",
    resource_files = glob(["src/main/res/**"]),
    deps = [":kotlin_app_lib"],
)
