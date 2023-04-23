/* eslint-disable */

import "./message.css";
import moment from "moment";

export default function Message(props = {user: {nom: "", avatar: ""}, ts: 0, content: ""}) {
    console.log(props);
    return (
        <div className={"message"}>
            <img src={props.user.avatar.replace(/\.gif/g,".png")} alt={"Avatar de " + props.user.nom} className={"avatar"} />
            <div className={"content"}>
                <h3>{props.user.nom}</h3>
                <p>{props.content}</p>
                <p className={"timestamp"}>{moment(props.ts).format("DD/MM/YYYY à HH:mm:ss")}</p>
            </div>
        </div>
    );
}
