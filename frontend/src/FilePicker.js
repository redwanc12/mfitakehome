import React, {useState} from 'react'
import { FileDrop } from 'react-file-drop'
import { Typography } from '@mui/material';
import "./f.css"
import axios from 'axios'
import CenteredTabs from "./Table"
import NoteAddOutlinedIcon from '@mui/icons-material/NoteAddOutlined';
import CircularProgress from '@mui/material/CircularProgress';
import { useNavigate } from "react-router-dom";
import Alert from '@mui/material/Alert';

export default function FilePicker() {
    const [data, setData] = useState()
    const [file, setFile] = useState()
    const [alert, setAlert] = useState(["info", "", false])
    let navigate = useNavigate(); 

    const changeHandler = async(files, event) => {
      setAlert(["info", "", false])
      if(typeof files[0] === "undefined" || files[0].type != "text/xml"){
        setAlert(["error", "File not supported", true])
        return
      }
      if (files[0]) {
        const url = "http://127.0.0.1:8000/"
        const data = new FormData() 
        data.append('upload_file', files[0])
        setFile(files[0])
        try{
          const res = await axios.post(url, data)
          if(res){
              setData(res.data)
          }; 
        } catch(error){
          console.log(error)
        }
      }
    }
    const discard = () => {
      if(window.confirm("Are you sure you want to discard this batch?")){
        setData()
        setFile()
        navigate(0)
      }
    }
    const approveBatch = async() => {
      if(window.confirm("Are you sure you want to approve this batch?")){
        const url = "http://127.0.0.1:8000/"
        const data = new FormData() 
        data.append('upload_file', file)
        try{
          const response = await axios.post(url+"approve/", data)
          if(response){
            navigate("/reports")
            navigate(0)
          }
      } catch(error){
        console.log(error)
      }
      }
    }
    const approveHandler = async() => {
      approveBatch()
      setData()
      setFile()
      setAlert(["success", "Success! You will now be redirected.", true])
      setTimeout(() => {
        navigate('/reports')
      }, 3000)
    }

    return (
    <React.Fragment>
        <Typography mt="20px" variant={'h4'} align="center">New Payment</Typography>
        {alert[2] && <Alert severity={alert[0]}>{alert[1]}</Alert>}
        {data? 
        <div style={{marginTop:"20px"}}><CenteredTabs onApprove={approveHandler} onDiscard={discard} data={data}/></div>:
        <div style={{border:"1px dashed grey", marginTop:"20px"}}>
          {!alert[2] &&
          <FileDrop
            onDrop={(files, event) => changeHandler(files, event)}
            >
              {file? <CircularProgress />:<NoteAddOutlinedIcon />}
              <Typography>Drag and Drop XML file</Typography> 
          </FileDrop>
          }
        </div>
        }
    </React.Fragment>
    );
}

