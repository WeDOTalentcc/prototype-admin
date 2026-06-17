# frozen_string_literal: true

class LanguageLevelSerializer
  def self.serialize(levels)
    {
      data: levels.each_with_index.map { |level, index|
        {
          id: index.to_s,
          type: "language_level",
          attributes: { name: level, id: index }
        }
      }
    }
  end
end
