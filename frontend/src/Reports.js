import * as React from 'react';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import DownloadIcon from '@mui/icons-material/Download';
import axios from 'axios'

export default function Reports(props) {
  const [anchorEl, setAnchorEl] = React.useState(null);
  const open = Boolean(anchorEl);
  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const downloadCsv = (type) => {
    const data = new FormData() 
    data.append('type', type)
    data.append('batch_id', props.batch_id)
    try{
    axios({
      url: 'http://127.0.0.1:8000/getCsv/',
      method: 'POST',
      data:data,
      responseType: 'blob', 
    }).then((response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', type+'_'+props.batch_id+'.csv');
      document.body.appendChild(link);
      link.click();
    });
    } catch(error){
      console.log(error)
    }
    setAnchorEl(null);
  }
  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <div>
      <Button
        id="basic-button"
        aria-controls={open ? 'basic-menu' : undefined}
        aria-haspopup="true"
        aria-expanded={open ? 'true' : undefined}
        onClick={handleClick}
        variant="outlined"
        disabled={props.status == "INITIALIZING"}
      >
      CSV
      <DownloadIcon />
      </Button>
      <Menu
        id="basic-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          'aria-labelledby': 'basic-button',
        }}
      >
        <MenuItem onClick={() => {downloadCsv('sources')}}>Source</MenuItem>
        <MenuItem onClick={() => {downloadCsv('branches')}}>Branch</MenuItem>
        <MenuItem onClick={() => {downloadCsv('payments')}}>Payments</MenuItem>
      </Menu>
    </div>
  );
}