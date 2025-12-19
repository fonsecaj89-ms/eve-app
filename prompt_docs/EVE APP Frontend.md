# Part 2: Frontend & Testing Prompt

# Part 2.1 Frontend structure and Tunnel setup
**Context:** You are a Senior Frontend Developer specializing in React and Data Visualization. You are building the UI for the EVE App.

**Tech Stack:**

- **Framework:** React 18+ (Vite), TypeScript.
    
- **Styling:** Tailwind CSS. EVE Theme.
    
- **State Management:** TanStack Query (React Query).
    
- **Routing:** React Router.
    

**Task:** Develop the frontend application and Swagger documentation.

## 1. Configuration & Networking

- **Vite Config:** `server.host: '0.0.0.0'`, `server.port: 5173`. HMR must work behind Cloudflare tunnel (`https://eve-app.jf-nas.com`).
    
- **API Client:** Axios with interceptors for 401 (Logout) and 429 (Global Lockdown).
    

## 2. UI Structure & Components

### A. Main Layout

- **Sidebar:** Fixed left navigation:
    
    - Dashboard
        
    - Market View
        
    - Search Item
        
    - Contracts
        
- **Top Bar:**
    
    - Character Portrait (Circular) - **Must use Local API**.
        
    - Name
        
    - Logout Button
        
    - ESI Status Indicator.
        

### B. Dashboard View

- Grid layout: Character Info, Wallet (ISK/PLEX), Skills Queue, Taxes/Standings.
    

### C. Market View

- **Filter Bar:** Tabs (Station, Region, Global), Category Filter, SCAN Button (with progress bar).
    
- **Data Table:**
    
    - **Item Icon:** Must use local proxy.
        
    - Columns: Item Name, Buy/Sell Station & Price, **Profit %**, Route Button.
        

### D. Search Item View

- **Autocomplete:** Fetch suggestions from backend.
    
- **Results:**
    
    - Large Item Image (Render/Icon) - **Must use Local API**.
        
    - Description.
        
    - Market Data Table.
        

### E. Contracts View

- **Card Grid Layout:**
    
    - Ship Contracts: Ship Image (Local API) + Fitted modules (Local API icons).
        
    - Bulk/Item Contracts: Main item image (Local API).
        
    - BPO/BPC: Green highlight.
        
- **Footer:** Price, "Jita Profit", "Copy Link".
    

### F. Route Popup

- Display Empire/Alliance logos for the systems if applicable (Local API).
    
- Risk Visualization (High kills/Smartbombs).
    

## 3. Visual Assets (Strict Requirement)

- **Local Image Proxy:**
    
    - **NEVER** use `https://images.evetech.net` directly in `<img>` tags.
        
    - **ALWAYS** use the backend proxy for ALL visual elements:
        
        - **Items:** `http://192.168.1.17:7777/api/images/type/{type_id}`
            
        - **Characters:** `http://192.168.1.17:7777/api/images/character/{char_id}`
            
        - **Corporations:** `http://192.168.1.17:7777/api/images/corporation/{corp_id}`
            
        - **Alliances:** `http://192.168.1.17:7777/api/images/alliance/{alliance_id}`
            
    - This is to ensure all images are cached in Postgres and compliant with the "Save Tokens" requirement.
        

## 4. Swagger & Testing

- Verify Swagger UI at `/docs`.
    
- **Input Validation:** Zod schemas matching Pydantic models. Mock data for testing
    
- **Theme:** Modern Dark Mode default (EVE Online aesthetics).

- **Login Test** Open the browser and validate the Login view displays the EVE SSO button pointing to the EVE SSO URL.

- **User Test** Notify the user to complete to start manual login and authorization process. After the manual login is completed, validate the session cached in Redis.

- **Dashboard Test** After redis validation, Open the browser and validate the Dashboard view opens.


# Part 2.2: 
**Context:** You are a Fullstack Developer specializing in React, Data Visualization and Backend Python Developer. You are integrating the frontend with the backend for the EVE App.

## 1. Project cleaning.

- Remove all unused files and folders.
- Remove all mocked data

## 2. API Integration.

- Integrate the backend API with the frontend.

