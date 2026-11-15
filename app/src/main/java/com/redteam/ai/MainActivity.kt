package com.redteam.ai

import android.app.Activity
import android.os.Bundle
import android.content.Intent
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView

class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val status = TextView(this).apply {
            text = "REDTEAM AI"
            textSize = 24f
            setPadding(20, 40, 20, 40)
        }

        val start = Button(this).apply {
            text = "INICIAR REDTEAM AI"
            setOnClickListener {
                val intent = Intent(this@MainActivity, RedteamService::class.java)
                startForegroundService(intent)
                status.text = "REDTEAM AI iniciando..."
            }
        }

        val stop = Button(this).apply {
            text = "PARAR REDTEAM AI"
            setOnClickListener {
                stopService(Intent(this@MainActivity, RedteamService::class.java))
                status.text = "REDTEAM AI parada"
            }
        }

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 40, 24, 24)
            addView(status)
            addView(start)
            addView(stop)
        }
        setContentView(layout)
    }
}
