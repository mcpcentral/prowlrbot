export interface MarketplaceListing {
  id: string;
  title: string;
  name: string;
  description: string;
  category: string;
  version: string;
  rating: number;
  ratingCount: number;
  downloads: number;
  price: number;
  tags: string[];
  trustTier: string;
  authorName: string;
  authorUrl: string;
  authorAvatarUrl: string;
  sourceRepo: string;
  license: string;
  changelog: string;
  compatibility: string;
  difficulty: string;
  installed?: boolean;
}

export interface Bundle {
  id: string;
  name: string;
  description: string;
  emoji: string;
  color: string;
  listing_ids: string[];
  install_count: number;
}

export interface ListingDetail {
  listing: MarketplaceListing;
  install_command: string;
  tip_total: number;
  reviews: ReviewEntry[];
  bundles: string[];
  related: MarketplaceListing[];
  author_listings: MarketplaceListing[];
}

export interface ReviewEntry {
  id: string;
  listing_id: string;
  reviewer_id: string;
  rating: number;
  comment: string;
  created_at: string;
}
