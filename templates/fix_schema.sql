-- First, let's see what we're dealing with
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE 'myapp_%';

-- Drop problematic tables that might be causing issues
DROP TABLE IF EXISTS myapp_review CASCADE;
DROP TABLE IF EXISTS myapp_adminlog CASCADE;

-- Fix tradewisecard table
DO $$ 
BEGIN
    -- Check if user_id column exists in tradewisecard
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='myapp_tradewisecard' AND column_name='user_id') THEN
        ALTER TABLE myapp_tradewisecard ADD COLUMN user_id INTEGER REFERENCES auth_user(id);
        RAISE NOTICE 'Added user_id to myapp_tradewisecard';
    ELSE
        RAISE NOTICE 'user_id already exists in myapp_tradewisecard';
    END IF;
END $$;

-- Fix tradewisecoin table  
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='myapp_tradewisecoin' AND column_name='user_id') THEN
        ALTER TABLE myapp_tradewisecoin ADD COLUMN user_id INTEGER REFERENCES auth_user(id);
        RAISE NOTICE 'Added user_id to myapp_tradewisecoin';
    END IF;
END $$;

-- Fix blogpost table
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='myapp_blogpost' AND column_name='slug') THEN
        ALTER TABLE myapp_blogpost ADD COLUMN slug VARCHAR(255);
        RAISE NOTICE 'Added slug to myapp_blogpost';
    END IF;
END $$;

-- Fix testimonial table
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='myapp_testimonial' AND column_name='is_approved') THEN
        ALTER TABLE myapp_testimonial ADD COLUMN is_approved BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added is_approved to myapp_testimonial';
    END IF;
END $$;

-- Reset migration history for myapp
DELETE FROM django_migrations WHERE app = 'myapp';