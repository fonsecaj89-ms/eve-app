export interface CharacterSession {
    character_id: number;
    character_name: string;
    authenticated: boolean;
}

export interface RouteWaypoint {
    system_id: number;
    name: string;
    security: number;
}

export interface MarketOrder {
    order_id: number;
    type_id: number;
    price: number;
    volume_remain: number;
    is_buy_order: boolean;
    location_id: number;
}
