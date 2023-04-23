/* eslint-disable */

import { useState, useRef } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import moment from 'moment'
import Message from "./components/Message.jsx";

function App() {

  const [file, setFile] = useState(null)
    const [data, setData] = useState(null)
  const fileInputRef = useRef(null)

    const user = (id) => {
        return data["utilisateurs"][id]
    }

  return (
    <>
        {
            !data ? <div className={"App"}>
                <h1>Importez le fichier JSON juste ici:</h1>
                <input ref={fileInputRef} type="file" id="file" name="file" onChange={(e) => setFile(e.target.files[0])} />
                <button onClick={
                    () => {
                        fileInputRef.current.click()
                    }
                }>Importer</button>
                <p>{file?.name}</p>
                <button onClick={
                    () => {
                        // Read
                        const reader = new FileReader()
                        reader.onload = (e) => {
                            const json = JSON.parse(e.target.result)
                            if (!json["ouvert_par"] || !json["ouvert_timestamp"] || !json["transcript"] || !json["utilisateurs"]) {
                                alert("Le fichier JSON n'est pas valide.")
                                return
                            }
                            console.log(json)
                            // Pretty-log
                            setData(json)
                        }
                        reader.readAsText(file)
                    }
                }>Valider</button>
            </div> : <div className={"displayTicket"}>
                <h1 className={"d_t_d"}>Ticket de {user(data["ouvert_par"])?.nom}</h1>
                <p className={"d_t_o"}>Ouvert le {moment(data["ouvert_timestamp"]).format("DD/MM/YYYY à HH:mm:ss")}</p>
                {
                    data["transcript"].map((info, index) => {
                        if (info.type == "message") {
                          return <Message user={user(info.utilisateur)} content={info.message} ts={info.timestamp} />
                        } else if (info.type == "ajout") {
                          return <p className={"d_t_o withSep"}>➡️ {user(info.par)?.nom} a ajouté {user(info.utilisateur).nom} ({moment(info.timestamp).format("DD/MM/YYYY à HH:mm:ss")})</p>
                        } else if (info.type == "retrait") {
                            return <p className={"d_t_o withSep"}>⬅️ {user(info.par)?.nom} a retiré {user(info.utilisateur).nom} ({moment(info.timestamp).format("DD/MM/YYYY à HH:mm:ss")})</p>
                        }
                    })
                }
            </div>
        }
    </>
  )
}

export default App
