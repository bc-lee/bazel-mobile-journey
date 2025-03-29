load("@rules_apple//apple:ios.bzl", "ios_application")
load("@rules_swift//swift:swift.bzl", "swift_library")

swift_library(
    name = "SimpleSwiftAppLib",
    srcs = glob(["Sources/**/*.swift"]),
    module_name = "SimpleSwiftApp",
    target_compatible_with = ["@platforms//os:ios"],
    visibility = ["//visibility:public"],
)

ios_application(
    name = "SimpleSwiftApp",
    bundle_id = "com.example.SimpleSwiftApp",
    bundle_name = "SimpleSwiftApp",
    families = [
        "iphone",
        "ipad",
    ],
    infoplists = [":Info.plist"],
    minimum_os_version = "15.0",
    resources = [
        "Sources/LaunchScreen.storyboard",
    ],
    visibility = ["//visibility:public"],
    deps = [":SimpleSwiftAppLib"],
)
