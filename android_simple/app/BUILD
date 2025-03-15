load("@rules_android//android:rules.bzl", "android_binary")

android_binary(
    name = "simple_android_app",
    srcs = glob(["src/main/java/**/*.java"]),
    custom_package = "com.example.simple",
    manifest = "src/main/AndroidManifest.xml",
    resource_files = glob(["src/main/res/**"]),
)
