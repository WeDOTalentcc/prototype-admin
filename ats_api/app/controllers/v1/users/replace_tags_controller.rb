module V1
  module Users
    class ReplaceTagsController < ApplicationController
      def index
        entities = params[:entities] || []
        replace_tags = []

        entities.each do |entity|
          tags = Dispatch.tag_array[entity.to_sym] || []
          replace_tags.concat(tags.map.with_index { |tag_info, index| OpenStruct.new(tag_info.merge(id: "#{entity}_#{index}")) })

          custom_tags = Dispatch.custom_replace_tags.select { |tag_info| tag_info[:entity].underscore.to_sym == entity }
          replace_tags.concat(custom_tags.map.with_index { |tag_info, index| OpenStruct.new(tag_info.merge(id: "#{entity}_custom_#{index}")) })
        end

        render_success(replace_tags, serializer: ReplaceTagSerializer)
      end
    end
  end
end
