import {spawnSync} from 'node:child_process';
const result=spawnSync('python3',['scripts/scudo360_geovision_adapter.py'],{stdio:'inherit',timeout:110000});
if(result.error)console.error('SCUDO_GEO_ERROR',String(result.error));
process.exitCode=result.status===0&&!result.error?0:1;
