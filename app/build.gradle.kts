plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.redteam.ai"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.redteam.ai"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }
}

chaquopy {
    defaultConfig {
        version = "3.14"
        pip {
            install("requests")
            install("httpx")
            install("beautifulsoup4")
            install("PyYAML")
        }
    }
}
