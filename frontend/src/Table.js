import * as React from 'react';
import Box from '@mui/material/Box';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import PrevTable from "./PrevTable";
import { Typography } from '@mui/material'
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';

export default function CenteredTabs(props) {
  const [value, setValue] = React.useState(0);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };
  const mapper = ['sources', 'branches']
  return (
    <Box sx={{ width: '100%', bgcolor: 'background.paper' }}>
      <Typography align="center">
        Total cost: ${parseFloat(props['data']['total_cost']).toLocaleString()} amongst {props['data']['total_payments'].toLocaleString()} payments
      </Typography>
      <Stack mt="10px" direction="row" spacing={2}>
        <Button onClick={props['onApprove']} variant="contained" style={{backgroundColor:"#DA1884"}}>
          Approve
        </Button>
        <Button onClick={props['onDiscard']} variant="contained" style={{backgroundColor:"#653819"}}>
          Discard
        </Button>
    </Stack>
      <Tabs value={value} onChange={handleChange} centered>
        <Tab label="Source" />
        <Tab label="Branch" />
      </Tabs>
    <PrevTable data={props['data'][mapper[value]]}/>
    </Box>

  );
}