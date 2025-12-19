import { useState, useEffect } from 'react'
import logger from './utils/logger'

function App() {
    const [data, setData] = useState(null)
    const apiUrl = import.meta.env.VITE_API_URL

    useEffect(() => {
        logger.info('App mounted', { apiUrl })
        fetch(`${apiUrl}/`)
            .then(res => res.json())
            .then(data => {
                logger.info('Backend response', data)
                setData(data)
            })
            .catch(err => logger.error('Backend connection failed', err))
    }, [apiUrl])

    return (
        <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
            <h1>EVE App Frontend</h1>
            <p>Backend Status: {data ? data.message : 'Connecting...'}</p>
        </div>
    )
}

export default App
