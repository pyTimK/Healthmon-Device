from typing import Dict, List, Optional
from google.cloud import texttospeech as tts
from funcs import normal_measures, normal_temp, normal_pulse, normal_spo2
import subprocess
from check_internet import has_internet

_result_auido_loc = "/home/pi/Desktop/tts_result.mp3"

# Instantiates a client
_client = tts.TextToSpeechClient()


# Build the voice request, select the language code ("en-US") and the ssml
# voice gender ("neutral")
_voice = tts.VoiceSelectionParams(
    language_code="fil-PH",

    #TODO CHANGE TO WAVENET ON FINAL
    #name="fil-PH-Standard-A",
    name="fil-PH-Wavenet-D",
)



# Select the type of audio file you want returned
_audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.MP3)


# The response's audio_content is binary.
def _save_tts(response: tts.SynthesizeSpeechResponse):
    with open(_result_auido_loc, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print(f'Successfully converted audio to file {_result_auido_loc}')


def _convert(*texts: str):
    synthesis_input = tts.SynthesisInput(text=" ".join(texts))

    response = _client.synthesize_speech(input=synthesis_input, voice=_voice, audio_config=_audio_config)
    
    _save_tts(response)


normal_result_mapping = {
    -1: "Mas mababa kaysa normal. ",
    0: "Ito ay normal. ",
    1: "Higit kaysa normal. ",
}

def _generate_message_text(health_workers: List[Dict]):
    addressing_text = 'kay' if len(health_workers) < 2 else 'kina'
    health_workers_text = ""
    if len(health_workers) == 0:
        return ""
    
    if len(health_workers) == 1:
        health_workers_text = health_workers[0]["name"]
    else:
        i = 0
        for i in range(len(health_workers) - 2):
            health_workers_text += f"{health_workers[i]['name']}, " 

        health_workers_text += f"{health_workers[len(health_workers)-2]['name']} at {health_workers[len(health_workers)-1]['name']}"

    return f"Ipinapadala ko na ang mensaheng ito {addressing_text} {health_workers_text}."

def _generate_string_to_speak(temp: float, pulse: int, spo2: int, user: Dict):
    name: str = user["name"]
    
    temp_text = f"Ang iyong temperatura {name} ay {temp:.1f} degree celsius. "
    temp_analysis_text = normal_result_mapping[normal_temp(temp)]
    pulse_text = f"Ang iyong pulso ay tumitibok ng {pulse} beses bawat minuto. "
    pulse_analysis_text = normal_result_mapping[normal_pulse(pulse)]
    spo2_text = f"Ang saturasyon ng oxygen sa iyong dugo ay {spo2} porsyento. "
    spo2_analysis_text = normal_result_mapping[normal_spo2(spo2)]
    message_text = "" if (normal_measures(temp, pulse, spo2) or len(user["healthWorkers"]) == 0) else _generate_message_text(user["healthWorkers"])
    print(message_text)
    return temp_text + temp_analysis_text + pulse_text + pulse_analysis_text + spo2_text + spo2_analysis_text + message_text


print_failed_convert = lambda : print("Failed to convert text to speech")

def speak_results(temp: float, pulse: int, spo2: int, user: Dict):
    if (not has_internet()):
        print_failed_convert()
        return

    try:
        print("About to convert result text to speech...")
        
        _convert(_generate_string_to_speak(temp, pulse, spo2, user))

    except Exception as e:
        print(e)
        print_failed_convert()
        return
    
    try:
        subprocess.run(["mpg123", _result_auido_loc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(e)
        print("Failed to converted audio")


#TESTING-------------
#speak_results(34.1, 77, 99, {"confirmed": True, "new_id": "", "id": "v9zsngsAZ5M5MyRIKIKsVZzyquq1", "new_name": "", "request_timestamp": "2022-02-06 09:03:24.732000+00:00", "name": "Mikee", "healthWorkers": [{"number": "09185626400", "id": "gZcLj8q48iS7ln0ZBO5YXFSNl933", "name": "Krisha ", "photoURL": "https://lh3.googleusercontent.com/a-/AOh14GhDD38dU8BOSjUN0Qd6rYfRPV--4EAulGXsHbLD7A=s96-c"}, {"number": "09683879596", "id": "drtsFBmjurSd8ca2Hkjqdnduxgm1", "photoURL": "https://lh3.googleusercontent.com/a-/AOh14GhonvrLgn3bOEU0RTbALsosITej_qDE4iedZ4BY=s96-c-rg-br100", "name": "Tim Mua123231"}, {"number": "09466583398", "photoURL": "https://lh3.googleusercontent.com/a/AATXAJxDS2TkxNgsl_0FgkpUyp1xMrSaRYreJupN0q8a=s96-c", "id": "faZPUadJv6QHixfnVehCoIdBiv92", "name": "Louren"}, {"photoURL": "", "name": "Sophia Belen", "id": "U8PJuEbvF6QFtAxm8cDVBLumPbD2", "number": "09564497810"}]})


#--------------------
