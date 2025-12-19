import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Utility for merging classes
function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

type ResourceType = 'type' | 'character' | 'corporation' | 'alliance';

interface EveImageProps extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'id'> {
    id: number | string;
    type: ResourceType;
    baseSize?: number; // Just for sizing reference, not used in URL per backend logic
}

export const EveImage: React.FC<EveImageProps> = ({ id, type, className, baseSize = 64, alt, ...props }) => {
    // STRICT LOCAL PROXY USAGE
    // Backend URL: http://192.168.1.17:7777/api/images/{type}/{id}
    // We use the environment variable for flexbility but default to the requirement.

    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const src = `${baseURL}/api/images/${type}/${id}`;

    return (
        <img
            src={src}
            alt={alt || `${type} ${id}`}
            className={cn("rounded-md bg-eve-panel/50 border border-eve-border/30", className)}
            loading="lazy"
            {...props}
        />
    );
};
